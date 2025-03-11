import os
import csv
from app.models import Admin
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import Paginator
from django.db import connection
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

def handle_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            admin_user = Admin.objects.get(username=username)
            if check_password(password, admin_user.password):
                request.session['admin_id'] = admin_user.id
                request.session['admin_username'] = admin_user.username
                return True
            else:
                messages.error(request, 'Invalid username or password')
        except Admin.DoesNotExist:
            messages.error(request, 'Invalid username or password')
    return False

def main_view(request):
    if request.session.get('admin_id'):
        return render(request, 'main.html')
    else:
        if handle_login(request):
            return redirect('main')
        return render(request, 'login.html')

def login_view(request):
    if request.session.get('admin_id'):
        return redirect('main')
    else:
        if handle_login(request):
            return redirect('main')
        return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('main')

def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        password2 = request.POST["password2"]
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")
        if Admin.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")
        user = Admin.objects.create(username=username, password=make_password(password))
        user.save()
        messages.success(request, "Registration successful!")
        return redirect("login")
    return render(request, "register.html")

def account_view(request):
    if not request.session.get('admin_id'):
        return redirect('main')
    columns = [field.name for field in Admin._meta.fields if field.name != 'password']
    rows = Admin.objects.all()
    context = {
        'columns': columns,
        'rows': rows,
    }
    return render(request, 'account.html', context)

def account_add_view(request):
    if not request.session.get('admin_id'):
        return redirect('main')
    if request.method == 'POST':
        try:
            admin_data = {key: value for key, value in request.POST.items() if key != 'csrfmiddlewaretoken'}
            admin_data['password'] = make_password(admin_data['password'])
            Admin.objects.create(**admin_data)
            messages.success(request, 'Admin added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding admin: {e}')
    return redirect('account')

def get_all_tables():
    with connection.cursor() as cursor:
        tables = connection.introspection.get_table_list(cursor)
    return [table.name for table in tables]

def get_non_empty_excluded_tables(excluded_tables):
    empty_tables = []
    with connection.cursor() as cursor:
        for table in excluded_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count == 0:
                    empty_tables.append(table)
            except Exception as e:
                print(f"Error checking table {table}: {e}")
    return empty_tables

def get_table_info(table_name):
    with connection.cursor() as cursor:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            cursor.execute("SELECT pg_size_pretty(pg_relation_size(%s))", [table_name])
            size = cursor.fetchone()[0]
        except Exception:
            row_count = 'N/A'
        try:
            db_engine = connection.settings_dict['ENGINE']
            if 'sqlite' in db_engine:
                cursor.execute(f"PRAGMA table_info({table_name})")
                col_count = len(cursor.fetchall())
            elif 'postgresql' in db_engine:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                """, [table_name])
                col_count = cursor.fetchone()[0]
            elif 'mysql' in db_engine:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                      AND table_schema = DATABASE()
                """, [table_name])
                col_count = cursor.fetchone()[0]
            else:
                col_count = 'N/A'
        except Exception:
            col_count = 'N/A'
    return row_count, col_count, size

def data_view(request):
    if not request.session.get('admin_id'):
        return redirect('main')
    tables = get_all_tables()
    default_tables = [
        'app_admin',
    ]
    system_tables = [
        'auth_group',
        'auth_group_permissions',
        'auth_permission',
        'auth_user',
        'auth_user_groups',
        'auth_user_user_permissions',
        # 'django_admin_log',
        'django_content_type',
        'django_migrations',
        'django_session',
    ]
    merge_tables = default_tables + system_tables
    if request.GET.get('system') == 'show':
        empty_tables = get_non_empty_excluded_tables(merge_tables)
        tables = [table for table in tables if table not in empty_tables]
    else:
        tables = [table for table in tables if table not in merge_tables]
    table_data = []
    for table in tables:
        row_count, col_count, size = get_table_info(table)
        table_data.append({
            'name': table,
            'row_count': row_count,
            'col_count': col_count,
            'size': size,
        })
    return render(request, 'data.html', {'tables': table_data})

def table_add(request):
    if request.method == 'POST':
        table_name = request.POST.get('tableName').strip()
        columns = request.POST.get('columns', '').strip()
        if not any(col.split()[0] == 'id' for col in columns.split(',') if col.strip()):
            columns = f"id SERIAL PRIMARY KEY, {columns}" if columns else "id SERIAL PRIMARY KEY"
        formatted_columns = []
        for column in columns.split(','):
            column_name = column.split()[0]
            if column_name.lower() != 'id':
                formatted_columns.append(f"{column_name} TEXT")
            else:
                formatted_columns.append(column)
        columns = ", ".join(formatted_columns)
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE TABLE {table_name} ({columns})")
        except Exception as e:
            messages.error(request, str(e))
            return HttpResponseRedirect(reverse('data_view'))
    return HttpResponseRedirect(reverse('data_view'))

def table_import(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csvFile')
        table_name = request.POST.get('tableName').strip()
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Only CSV files are allowed.')
            return render(request, 'data.html')
        if not table_name:
            table_name = os.path.splitext(csv_file.name)[0]
        try:
            with connection.cursor() as cursor:
                data = csv.reader(csv_file.read().decode('utf-8').splitlines())
                headers = next(data)
                if 'id' not in headers:
                    headers.insert(0, 'id')
                    id_column_added = True
                else:
                    id_column_added = False
                columns = ', '.join([f"{header} TEXT" for header in headers])
                if id_column_added:
                    columns = 'id SERIAL PRIMARY KEY, ' + ', '.join([f"{header} TEXT" for header in headers[1:]])
                cursor.execute(f"CREATE TABLE {table_name} ({columns})")
                for row in data:
                    if id_column_added:
                        placeholders = 'DEFAULT, ' + ', '.join(['%s'] * (len(row)))
                    else:
                        placeholders = ', '.join(['%s'] * len(row))
                    cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", row)
            return HttpResponseRedirect(reverse('data_view'))
        except Exception as e:
            messages.error(request, str(e))
            return render(request, 'data.html')
    return HttpResponseRedirect(reverse('data_view'))

def export_all(request):
    current_datetime = datetime.now().strftime('%Y%m%d%H%M%S')
    response = HttpResponse(content_type='application/sql')
    response['Content-Disposition'] = f'attachment; filename="backup_{current_datetime}.sql"'
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)
        tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s;", [table_name])
            columns = cursor.fetchall()
        create_table_query = f"CREATE TABLE {table_name} (\n"
        for i, column in enumerate(columns):
            column_name, data_type = column
            create_table_query += f"    {column_name} {data_type},\n" if i < len(columns) - 1 else f"    {column_name} {data_type}\n"
        create_table_query += ");\n\n"
        response.write(create_table_query)
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            column_names = [col[0] for col in cursor.description]
        for row in rows:
            insert_query = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join([repr(val) for val in row])});\n"
            response.write(insert_query)
        response.write("\n")
    return response

def table_export(request, table_name):
    try:
        file_name = request.GET.get('file_name', table_name)
        if not file_name:
            file_name = table_name
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
            columns = [row[0] for row in cursor.fetchall()]
        current_datetime = datetime.now().strftime('%Y%m%d%H%M%S')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{file_name}_{current_datetime}.csv"'
        writer = csv.writer(response)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(row)
        return response
    except Exception as e:
        messages.error(request, str(e))
        return render(request, 'data.html')

def table_drop(request):
    if request.method == 'POST':
        table_name = request.POST.get('tableName')
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE {table_name}")
            return HttpResponseRedirect(reverse('data_view'))
        except Exception as e:
            tables = get_all_tables()
            messages.error(request, str(e))
            return render(request, 'data.html', {'tables': tables})
    else:
        return HttpResponseRedirect(reverse('data_view'))

def table(request, table_name):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
    except Exception as e:
        messages.error(request, str(e))
        raise Http404(f"Error accessing table: {e}")
    paginator = Paginator(rows, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    current_page = page_obj.number
    total_pages = paginator.num_pages
    max_links = 10
    start_page = max(current_page - max_links // 2, 1)
    end_page = min(start_page + max_links - 1, total_pages)
    if end_page - start_page + 1 < max_links:
        start_page = max(end_page - max_links + 1, 1)
    page_range = range(start_page, end_page + 1)
    return render(request, 'table.html', {
        'table_name': table_name,
        'columns': columns,
        'rows': page_obj,
        'page_obj': page_obj,
        'page_range': page_range,
    })

def table_row(request, table_name):
    if request.method == 'POST':
        data = request.POST.dict()
        data.pop('csrfmiddlewaretoken', None) 
        columns = ', '.join(data.keys())
        values_placeholders = ', '.join(['DEFAULT'] + [f"%s" for _ in data.values()])
        try:
            with connection.cursor() as cursor:
                query = f"INSERT INTO {table_name} (id, {columns}) VALUES ({values_placeholders})"
                cursor.execute(query, list(data.values()))
            messages.success(request, f"New row added successfully to '{table_name}'.")
        except Exception as e:
            messages.error(request, f"Error adding row: {e}")
        return redirect('table_row', table_name=table_name)
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", [table_name])
            columns = [col[0] for col in cursor.fetchall()]
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
    except Exception as e:
        messages.error(request, f"Error fetching data: {e}")
        columns, rows = [], []
    paginator = Paginator(rows, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(page_number, on_each_side=1, on_ends=1)
    return render(request, 'table.html', {
        'table_name': table_name,
        'columns': columns,
        'rows': page_obj.object_list,
        'page_obj': page_obj,
        'page_range': page_range,
    })

def get_table_fields(table_name):
    with connection.cursor() as cursor:
        db_engine = connection.settings_dict['ENGINE']
        if 'sqlite' in db_engine:
            cursor.execute(f"PRAGMA table_info({table_name})")
            fields = [{'name': row[1], 'type': row[2]} for row in cursor.fetchall()]
        elif 'postgresql' in db_engine:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
            """, [table_name])
            fields = [{'name': row[0], 'type': row[1]} for row in cursor.fetchall()]
        elif 'mysql' in db_engine:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
            """, [table_name])
            fields = [{'name': row[0], 'type': row[1]} for row in cursor.fetchall()]
        else:
            fields = []
    return fields

def field_view(request, table_name):
    fields = get_table_fields(table_name)
    return render(request, 'field.html', {'table_name': table_name, 'fields': fields})

def field_add(request, table_name):
    if request.method == 'POST':
        column_name = request.POST.get('columnName')
        if not column_name:
            messages.error(request, "Column name cannot be empty.")
            return HttpResponseRedirect(reverse('field_view', args=[table_name]))
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT DEFAULT ''")
            messages.success(request, f"Column '{column_name}' added successfully.")
        except Exception as e:
            messages.error(request, f"Error adding column: {e}")
        return HttpResponseRedirect(reverse('field', args=[table_name]))
    messages.error(request, "Invalid request method.")
    return HttpResponseRedirect(reverse('field', args=[table_name]))