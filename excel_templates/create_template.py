#!/usr/bin/env python3
import xlsxwriter
import json
import sys
from datetime import date


def create_constraints(constraints, field):
    strings = []
    if 'enum' in constraints.keys():
        options = "\", \"".join(constraints.pop('enum'))
        strings.append(f"case sensitive restricted values: \"{options}\"")
    if field.get('name', '') == 'aread_id':
        strings.append('Must be an area_id from the agreed area hierarchy.')
    for k, v in constraints.items():
        strings.append(f"{k}: {v}")
    if strings == []:
        strings = ['none']
    return "|".join(strings)


def write_column_definitions_worksheet(worksheet, workbook,  schema):

    template_title = " | ".join([schema.get('title', ""), "Data Template"])
    title_format = workbook.add_format({'bold': True, 'font_size': 14})
    worksheet.merge_range('A1:F1', template_title, title_format)

    version_date = f"version {schema.get('version', 'n/a')}; {date.today()}"
    worksheet.merge_range('A3:F3', version_date)

    notes = f"Please use the following definitions to fill in the template overleaf. {schema.get('description', '')}"
    notes_format = workbook.add_format({'text_wrap': True, 'align': 'top'})
    worksheet.merge_range('A4:F4', notes, notes_format)

    headers = [
        'Field Name',
        'Field Description',
        'Data Type',
        'Required',
        'Other Constraints',
        'Unique Key **'
    ]
    headers_format = workbook.add_format({
        'bold': True,
        'bg_color': '#d9d9d9',
        'top': 1,
        'bottom': 1
    })
    for h in range(len(headers)):
        worksheet.write(6, h, headers[h], headers_format)

    fields = schema.get('fields', [])
    for f in range(len(fields)):
        field = fields[f]
        constraints = field.get('constraints', {}).copy()
        required = constraints.pop('required', False)
        required = 'Required' if required else 'Optional'
        other_constraints = create_constraints(constraints, field)
        key = 'TRUE' if field['name'] in schema.get('primaryKey', []) else ''
        row = [
            field['name'],
            field.get('description', ""),
            field['type'],
            required,
            other_constraints,
            key
        ]
        for c in range(len(row)):
            worksheet.write(7+f, c, row[c])
    top_border_format = workbook.add_format({'top': 1})
    for c in range(len(headers)):
        worksheet.write(7+f+1, c, "", top_border_format)

    r = 0
    if schema.get('custom-constraints'):
        headers = [
            'Further Contraints',
            'Condition',
            'Explanation',
            'Required',
            'Other Constraints',
            'Unique Key **'
        ]
        headers_format = workbook.add_format({
            'bold': True,
            'bg_color': '#d9d9d9',
            'top': 1,
            'bottom': 1
        })
        worksheet.write(7+f+2, 0, 'Further Constraints', headers_format)
        worksheet.write(7+f+2, 1, 'Condition', headers_format)
        worksheet.merge_range(7+f+2, 2, 7+f+2, len(headers)-1, 'Explanation', headers_format)

        custom_constraints = schema.get('custom-constraints', [])
        for r in range(len(custom_constraints)):
            constraint = custom_constraints[r]
            row = [
                r+1,
                constraint['constraint'],
                constraint.get('explanation', 'None.'),
            ]
            vertical_center_format = workbook.add_format({'align': 'top'})
            worksheet.write(7+f+3+r, 0, r+1, vertical_center_format)
            worksheet.write(7+f+3+r, 1, constraint['constraint'], vertical_center_format)
            text_wrap_format = workbook.add_format({'text_wrap': True, 'align': 'top'})
            worksheet.merge_range(7+f+3+r, 2, 7+f+3+r, len(headers)-1, constraint.get('explanation', 'None.'), text_wrap_format)

        for c in range(len(headers)):
            worksheet.write(7+f+3+r+1, c, "", top_border_format)

    worksheet.merge_range(
        7+f+3+r+3, 0,
        7+f+3+r+3, len(headers)-1,
        '** For each row, the fields that contribute to the unique key must form a unique combination of values across the data set.',
        notes_format
    )


def write_data_template_worksheet(worksheet, workbook, schema):
    fields = schema.get('fields', [])
    headers_format = workbook.add_format({
        'bold': True,
        'bg_color': '#d9d9d9',
        'top': 1,
        'bottom': 1
    })
    for f in range(len(fields)):
        field = fields[f]
        worksheet.write(0, f, field['name'], headers_format)
        constraints = field.get('constraints', {})
        options = {}
        if 'minimum' in constraints.keys() and 'maximum' in constraints.keys():
            options = {
                'validate': 'integer',
                'criteria': 'between',
                'minimum': constraints['minimum'],
                'maximum': constraints['maximum']
            }
        elif 'minimum' in constraints.keys() and 'maximum' not in constraints.keys():
            options = {
                'validate': 'integer',
                'criteria': '>=',
                'value': constraints['minimum'],
            }
        elif 'maximum' in constraints.keys() and 'minimum' not in constraints.keys():
            options = {
                'validate': 'integer',
                'criteria': '<=',
                'value': constraints['maximum'],
            }
        elif 'enum' in list(constraints.keys()):
            options = {
                'validate': 'list',
                'source': constraints['enum']
            }
            if len(constraints['enum']) == 1:
                for i in range(1000):
                    worksheet.write(i+1, f, constraints['enum'][0])

        if options:
            worksheet.data_validation(1, f, 1000, f, options)


def create_template(schema_filename):
    with open(schema_filename, 'r') as schema_file:
        schema = json.load(schema_file)
    xlsx_filename = f"{schema_filename[:-5]}.xlsx"
    workbook = xlsxwriter.Workbook(xlsx_filename)
    column_def_worksheet = workbook.add_worksheet("Column Definitions")
    data_template_worksheet = workbook.add_worksheet("Data Template")

    write_column_definitions_worksheet(column_def_worksheet, workbook, schema)
    write_data_template_worksheet(data_template_worksheet, workbook, schema)

    workbook.close()


if __name__ == '__main__':
    files = sys.argv[1:]
    for file in files:
        try:
            create_template(file)
        except Exception as e:
            print(f"failed for {file}: {e}")