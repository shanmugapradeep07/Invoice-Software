import datetime
import json
import math
import os
import tkinter as tk
from tkinter import ttk, PhotoImage, Text, messagebox, scrolledtext

import jinja2
import pandas as pd
import pdfkit
import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from tkcalendar import DateEntry


def number_to_words(number):
    number = int(number)
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "Ten", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    if 0 <= number < 10:
        return ones[number]
    elif 10 <= number < 20:
        return teens[number - 10]
    elif 20 <= number < 100:
        return tens[number // 10] + (" " + ones[number % 10] if number % 10 > 0 else "")
    elif 100 <= number < 1000:
        return ones[number // 100] + " Hundred" + (" and " + number_to_words(number % 100) if number % 100 > 0 else "")
    elif 1000 <= number < 1000000:
        return number_to_words(number // 1000) + " Thousand" + (
            " " + number_to_words(number % 1000) if number % 1000 > 0 else "")
    elif 1000000 <= number < 1000000000:
        return number_to_words(number // 1000000) + " Million" + (
            " " + number_to_words(number % 1000000) if number % 1000000 > 0 else "")
    else:
        return "Number out of range"


# class TreeViewEdit(ttk.Treeview):
#     def __init__(self, master, **kw):
#         super().__init__(master,**kw)


class RecordEditorPopup:
    def __init__(self, master, record, popup_closed_callback):
        self.is_popped_up = False
        self.master = master
        self.record = record
        self.popup_closed_callback = popup_closed_callback

        self.popup = tk.Toplevel(master)
        self.popup.title("Dress Pattern Record")
        self.popup.protocol("WM_DELETE_WINDOW", self.on_popup_close)
        self.row_number = 0

        self.entry_vars = [tk.StringVar(value=value) for value in record.values()]
        self.row_number = 0
        for key, var in zip(record.keys(), self.entry_vars):
            if key == 'accessories':
                self.create_accessory_list(self.popup, record[key])
            else:
                field_name = " ".join(key.title().split('_'))
                label = tk.Label(self.popup, text=field_name)
                label.grid(row=self.row_number, column=0, padx=3, pady=3, sticky=tk.E)

                entry = tk.Entry(self.popup, textvariable=var)
                entry.grid(row=self.row_number, column=1, padx=3, pady=3)
            self.row_number += 1

        save_button = tk.Button(self.popup, text="Save", command=self.save_record)
        save_button.grid(row=len(self.entry_vars), column=0, columnspan=2, pady=3)

    def edit_selected_row(self, event):
        selected_item = self.popUpTreeview.selection()

        if selected_item:
            current_values = self.popUpTreeview.item(selected_item, 'values')
            new_values = self.get_user_input(current_values)
            if new_values:
                self.popUpTreeview.item(selected_item, values=new_values)
        else:
            print("Please select a row to edit.")

    # Function to get values from entry widgets when OK button is pressed
    def get_values(self):
        new_values = (
            self.accessory_entry.get(),
            self.quantity_entry.get(),
            self.price_entry.get()
        )
        self.new_values = new_values
        self.sencondPopup.destroy()
        return new_values

    def get_user_input(self, current_values):
        self.sencondPopup = tk.Toplevel()
        self.sencondPopup.title("Edit Row")
        self.new_values = None

        # Create entry widgets for the three data fields
        self.accessory_entry = ttk.Entry(self.sencondPopup)
        self.quantity_entry = ttk.Entry(self.sencondPopup)
        self.price_entry = ttk.Entry(self.sencondPopup)

        # Set initial values in the entry widgets
        self.accessory_entry.insert(0, current_values[0])
        self.quantity_entry.insert(0, current_values[1])
        self.price_entry.insert(0, current_values[2])

        # Add labels and entry widgets to the popup
        ttk.Label(self.sencondPopup, text="Accessory:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.accessory_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.sencondPopup, text="Quantity:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.quantity_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.sencondPopup, text="Price:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.price_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Add OK button to the popup
        ttk.Button(self.sencondPopup, text="OK", command=self.get_values).grid(row=3, column=0, columnspan=2, pady=10)

        self.sencondPopup.wait_window()  # Wait for the popup to be closed
        return self.new_values if self.new_values else current_values

    def create_accessory_list(self, root, datas):
        column_names = ["Accessory", "Quantity", "Price"]

        self.popUpTreeview = ttk.Treeview(root, columns=tuple(column_names), show='headings')

        # Configure column headings
        for i, column_name in enumerate(column_names):
            self.popUpTreeview.heading(column_name, text=column_name)
            if column_name in ['Quantity', 'Price']:
                self.popUpTreeview.column(column_name, width=60, anchor='center')  # Adjust the width as needed
            else:
                self.popUpTreeview.column(column_name, width=80, anchor='center')

        # Configure the Treeview widget to span the entire first column
        self.popUpTreeview.grid(row=self.row_number + 3, column=0, columnspan=3, padx=3, pady=3, sticky='nsew')

        for layer_data in datas:
            self.popUpTreeview.insert("", "end", values=layer_data)
        self.popUpTreeview.bind('<Double-1>', self.edit_selected_row)

    def save_record(self):
        updated_record = [var.get() for var in self.entry_vars]
        tuple_datas = []
        tuple_sum = 0
        for child_item_id in self.popUpTreeview.get_children():
            values = self.popUpTreeview.item(child_item_id, 'values')
            try:
                tuple_sum += int(values[2])
            except:
                pass
            tuple_datas.append(values)
        updated_record[-1] = tuple_datas
        print(updated_record)

        sum_value = 0
        for n, value in enumerate(updated_record[5:-1], start=5):
            if n in [6, 8]:
                continue
            sum_value += int(value)
        updated_record[3] = sum_value + tuple_sum
        self.popup.destroy()
        if self.popup_closed_callback:
            self.popup_closed_callback(updated_record)

    def on_popup_close(self):
        self.popup.destroy()
        if self.popup_closed_callback:
            self.popup_closed_callback(None)


class PurchaseInterface:
    def __init__(self):
        self.root = tk.Tk()
        self.INPUT_FILES_PATH = 'Input'
        self.INPUT_IMAGES_PATH = 'Input Pics'
        self.root.iconbitmap(f'{self.INPUT_IMAGES_PATH}/logo_.ico')

        self.create_date_entry()
        self.create_bill_no()
        self.create_vendor_name()
        self.create_item_name()
        self.create_numeric_quantity()
        # self.create_UOM()
        self.create_price_label()

    def create_date_entry(self):
        label = tk.Label(self.root, text="Date")
        label.grid(row=0, column=0, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        calendar = DateEntry(self.root, width=17, background="darkblue",
                             foreground="white", borderwidth=2)
        calendar.grid(row=0, column=1, padx=3, pady=3, sticky="e")
        calendar.config(font=("times new roman", 12))

    def create_bill_no(self):
        self.bill_no_var = tk.IntVar()
        other_cost_label = tk.Label(self.root, text="Bill No.", anchor="w", justify="left")
        other_cost_label.grid(row=1, column=0, padx=3, pady=3, sticky="e")
        other_cost_label.config(font=("times new roman", 12))

        other_cost_entry = tk.Entry(self.root, width=10, textvariable=self.bill_no_var, justify="right")
        other_cost_entry.grid(row=1, column=1, padx=3, pady=3, sticky="e")
        other_cost_entry.config(font=("times new roman", 12))

    def create_vendor_name(self):
        # df = self.client_df.loc[~self.client_df['Client Names'].isna()]

        # vendor_names = list(df['Client Names'].values)
        vendor_names = ['Vendor 1', 'Vendor 2']

        label = tk.Label(self.root, text='Vendor Name', anchor="w", justify="left")
        label.grid(row=2, column=0, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.client_name_var = tk.StringVar()
        client_name_combobox = ttk.Combobox(self.root, textvariable=self.client_name_var, values=vendor_names,
                                            state="readonly")
        client_name_combobox.set(vendor_names[0])
        client_name_combobox.grid(row=2, column=1, padx=3, pady=3, sticky="e")
        client_name_combobox.config(font=("times new roman", 12))

    def create_item_name(self):
        self.item_piece_var = tk.StringVar()
        piece_label = tk.Label(self.root, text="Item Name", anchor="w", justify="left")
        piece_label.grid(row=3, column=0, padx=3, pady=3, sticky="e")
        piece_label.config(font=("times new roman", 12))

        piece_entry = tk.Entry(self.root, width=15, textvariable=self.item_piece_var, justify="right")
        piece_entry.grid(row=3, column=1, padx=3, pady=3, sticky="e")
        piece_entry.config(font=("times new roman", 12))
        self.item_piece_var.set("")

    def create_numeric_quantity(self):
        label = tk.Label(self.root, text="Quantity:")
        label.grid(row=4, column=0, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.accessory_quantity_var = tk.IntVar()
        self.quantity_entry = tk.Spinbox(self.root, textvariable=self.accessory_quantity_var, from_=0, to=1000, width=5)
        self.quantity_entry.grid(row=4, column=1, padx=3, pady=3, sticky="e")
        self.quantity_entry.config(font=("times new roman", 12))

    def create_price_label(self):
        label = tk.Label(self.root, text="Cost/Mtr", anchor="w", justify="left")
        label.grid(row=5, column=0, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.price_var = tk.IntVar()
        price_entry = tk.Entry(self.root, textvariable=self.price_var, justify="right",
                               width=10)  # Change to Entry widget
        price_entry.grid(row=5, column=1, padx=3, pady=3, sticky="e")
        price_entry.config(font=("times new roman", 12))  # Apply the same font style


class BillInformationApp:
    def __init__(self, root):
        self.check_expiration_date()
        self.root = root
        self.current_app = None
        self.is_popped_up = False  # Flag to track if a pop-up is currently open

        self.INPUT_FILES_PATH = 'Input'
        self.INVOICE_PATH = 'Invoices'
        self.DETAILS_PATH = 'Bill Details'
        self.INPUT_IMAGES_PATH = 'Input Pics'
        self.DATABASE_PATH = 'Database'
        self.database_file = 'Invoice_Datas.json'
        self.excel_file = pd.ExcelFile(f"{self.INPUT_FILES_PATH}/User_Input_datas.xlsx")
        self.data_df = pd.read_excel(self.excel_file, 'Data & Assumption')
        self.stock_df = pd.read_excel(self.excel_file, 'Stock Statement')
        self.client_df = pd.read_excel(self.excel_file, 'Client Details')
        self.excel_file.close()
        self.pattern_price_hash_data = {}
        self.layer_price_hash_data = {}
        self.source_data_list = []
        self.accessory_data_dict = {}
        # self.invoice_data_fields = ['bill_no', 'bill_date', 'client_name', 'dress_pattern', 'piece_name', 'layer_name',
        #                             'layer_qnty', 'layer_price', 'machine_cost', 'embroidery_cost', 'dying_charges',
        #                             'other_cost', 'fixed_cost', 'accessory_name', 'accessory_qnty', 'accessory_price']
        self.invoice_data_fields = ['dress_pattern', 'piece_name', 'layer_name', 'total_cost'
                                                                                 'layer_qnty', 'layer_price',
                                    'machine_cost', 'embroidery_cost', 'dying_charges',
                                    'other_cost', 'fixed_cost', 'accessories']
        self.bill_no_integer = 1
        self.check_for_database_availability()

        self.update_layer_prices_hash_map(self.stock_df)
        self.update_piece_prices_hash_map(self.data_df)

        root.title("Malar Vikram")
        self.root.iconbitmap(f'{self.INPUT_IMAGES_PATH}/logo_.ico')

        self.row_number = 0
        self.piece_cost_sum = 0
        self.right_row_number = 0
        self.second_right_row_number = 0
        self.create_menu()

        self.create_bill_info_section()
        self.generate_bill_no()

        self.create_watermark()
        # self.style = ThemedStyle(self.root)  # Create a ThemedStyle instance
        # self.style.set_theme("plastik")  # Apply the "plastik" theme
        style = ttk.Style()
        style.theme_use("clam")  # vista
        """
        "clam": A light and simple theme.
        "alt": Another light theme, somewhat similar to "clam."
        "default": The default theme on most platforms, which may vary in appearance based on the operating system.
        "classic": The classic Tkinter theme, which has a traditional appearance.
        "vista": A theme that resembles the Windows Vista style.
        "xpnative": A theme that attempts to mimic the native look of Windows XP.
        "aquabutton": A macOS Aqua-style theme with round buttons and glossy appearance.
        """

        self.create_layer_input()
        # self.create_total_cost_for_layers()
        # self.create_total_cost_for_accessories()
        self.create_add_layer_button()
        self.create_layer_list()
        self.create_accessory_list()
        self.create_add_accessories_button()
        self.generate_in_voice_button()
        self.generate_save_details()
        self.refresh_datas()
        # self.show_purchase_interface()

        # self.create_watermark()

        self.machine_cost_var.trace("w", self.recalculate_total_cost)
        self.embroidery_cost_var.trace("w", self.recalculate_total_cost)
        self.embroidery_material_cost_var.trace("w", self.recalculate_total_cost)
        self.fixed_cost_var.trace("w", self.recalculate_total_cost)
        self.other_cost_var.trace("w", self.recalculate_total_cost)
        self.dying_var.trace("w", self.recalculate_total_cost)
        # self.total_layer_cost_var.trace("w", self.recalculate_total_cost)
        # self.total_accessory_cost_var.trace("w", self.recalculate_total_cost)

    def load_excel_datas(self):
        self.excel_file = pd.ExcelFile(f"{self.INPUT_FILES_PATH}/User_Input_datas.xlsx")
        self.data_df = pd.read_excel(self.excel_file, 'Data & Assumption')
        self.stock_df = pd.read_excel(self.excel_file, 'Stock Statement')
        self.client_df = pd.read_excel(self.excel_file, 'Client Details')
        self.excel_file.close()
        self.update_piece_prices_hash_map(self.data_df)
        self.update_layer_prices_hash_map(self.stock_df)
        self.reload_layer_dropdown()
        self.reload_dress_pattern_dropdown()
        self.reload_client_names_dropdown()
        self.reload_accessory_dropdown()

    @staticmethod
    def get_financial_year():
        today_date = datetime.datetime.today()
        cur_date = today_date.strftime('%Y-%mm-%dd')
        cur_year = today_date.year
        is_financial_year_running = cur_date >= f'{cur_year}-04-01'
        if is_financial_year_running:
            financial_year = f'{str(cur_year)[-2:]}-{str(cur_year + 1)[-2:]}'
        else:
            financial_year = f'{str(cur_year - 1)[-2:]}-{str(cur_year)[-2:]}'
        return financial_year

    def generate_bill_no(self):
        financial_year = self.get_financial_year()
        bill_format_type = f'MV/{financial_year}/{self.bill_no_integer}'
        self.bill_label.set(bill_format_type)
        self.bill_entry.config(state='disabled')

    def show_preview_bill_v1(self):
        text_widget = scrolledtext.ScrolledText(wrap=tk.WORD, font=("Courier", 10))
        text_widget.grid(row=8, column=7, columnspan=2, padx=3, pady=3)

        df = pd.DataFrame(self.source_data_list)
        result_df = df.groupby('dress_pattern')['total_cost'].sum().reset_index()
        total_age = df['total_cost'].sum()

        # Convert DataFrame to a formatted string
        df_string = result_df.to_string(index=False)

        # Insert the formatted string and age total into the text widget
        text_widget.insert(tk.END, f"{df_string}\n\nTotal Age: {total_age}")

    def save_json(self, json_data):
        """Saves json data of page. Takes 2 arguments json data and file name without extension"""
        html_path = os.path.join(os.getcwd(), self.DATABASE_PATH)  # html folder path
        if not os.path.exists(html_path):
            os.makedirs(html_path)
        json_file_name = os.path.join(html_path, self.database_file)
        json_obj = json.dumps(json_data, indent=3)
        with open(f'{json_file_name}', "w", encoding='utf-8') as file:
            file.write(json_obj)

    def open_json_file(self):
        '''Opens a html file and read it to return the soup of that page'''
        if os.path.exists(f"{self.DATABASE_PATH}/{self.database_file}"):
            with open(f"{self.DATABASE_PATH}/{self.database_file}", 'r') as f:  # Folder name should be Json in the cwd
                data = f.read()
                json_data = json.loads(data)
                return json_data
        return {}

    def check_for_database_availability(self):
        if os.path.exists(f"{self.DATABASE_PATH}/{self.database_file}"):
            database_datas = self.open_json_file()
            financial_year = self.get_financial_year()
            last_bill_no = database_datas.get(f'{financial_year}_last_bill_no', 0)
            self.bill_no_integer = int(last_bill_no) + 1
        else:
            self.bill_no_integer = 1

    def save_datas_to_database(self):
        financial_year = self.get_financial_year()
        last_num_key = f'{financial_year}_last_bill_no'

        if os.path.exists(f"{self.DATABASE_PATH}/{self.database_file}"):
            database_datas = self.open_json_file()
            current_data = {self.bill_entry.get(): self.source_data_list}
            database_datas['results'].append(current_data)
            database_datas[last_num_key] = self.bill_label.get().split('/')[-1]
            self.save_json(database_datas)
        else:
            result_datas = {
                'results': [{self.bill_entry.get(): self.source_data_list}],
                last_num_key: self.bill_label.get().split('/')[-1]
            }
            self.save_json(result_datas)

        self.bill_no_integer += 1
        self.generate_bill_no()

    def clear_datas(self):
        self.piece_var.set('')
        self.quantity_var.set(0.0)
        self.price_var.set(0)
        self.machine_cost_var.set(0)
        self.embroidery_var.set(0)
        self.machine_in_hours_var.set(0)
        self.embroidery_in_hrs_var.set(0)
        self.dying_var.set(0)
        self.other_cost_var.set(0)
        self.fixed_cost_var.set(0)
        self.accessory_price_var.set(0)
        self.accessory_quantity_var.set(0)

        self.clear_treeview(self.treeview)
        self.total_cost_var.set(0)
        self.total_cost_in_word.delete("1.0", tk.END)

    def create_invoice_pdf(self):
        self.save_datas_to_database()

        # self.show_preview_bill()
        company_details = pd.read_excel(f'{self.INPUT_FILES_PATH}/User_Input_datas.xlsx', 'Company Details')
        company_details.fillna('', inplace=True)
        client_name = self.client_name_var.get()

        client_details = self.client_df[self.client_df['Client Names'] == client_name]
        client_details.fillna('', inplace=True)

        client_data_dict = {}
        for data in client_details.iterrows():
            client_data_dict = data[1].to_dict()

        company_data_dict = {}
        for data in company_details.iterrows():
            company_data_dict = data[1].to_dict()

        price_variable = self.total_cost_var.get()
        tax_value = round(price_variable * 0.05, 2)
        total_value = price_variable + tax_value

        bill_no = self.bill_label.get()
        bill_date = self.calendar.get_date()
        formatted_date = bill_date.strftime("%d-%m-%Y")
        df = pd.DataFrame(self.source_data_list)
        result_df = df.groupby('dress_pattern')['total_cost'].sum().reset_index()

        dress_data_list = []
        for s_no, record in enumerate(result_df.iterrows(), start=1):
            data_dict = {'s_no': s_no}
            data_dict = {**data_dict, **record[1].to_dict()}
            dress_data_list.append(data_dict)

        customer_details = {
            'company_name': company_data_dict['Name'],
            'address_line_1': company_data_dict['Address_Line_1'],
            'address_line_2': company_data_dict['Address_Line_2'],
            'gstn_no': company_data_dict['GSTN'],
            'name': client_name,
            'bill_no': bill_no,
            'bill_date': formatted_date,
            'state': client_data_dict['State'],
            'email_id': client_data_dict['Email'],
            'phone_number': client_data_dict['Phone Number'],
            'dress_records': dress_data_list,
            'other_charges': tax_value,
            'amount_receivable': total_value,
            'invoice_value': total_value,
            'total_cost_for_client': price_variable,
        }

        template_loader = jinja2.FileSystemLoader('./')
        template_env = jinja2.Environment(loader=template_loader)

        template = template_env.get_template(f"{self.INPUT_FILES_PATH}/invoice_template.html")

        output_text = template.render(records=customer_details)

        config_df = pd.read_excel(f'{self.INPUT_FILES_PATH}/User_Input_datas.xlsx', 'Configs')

        type = 'whtmltopdf'
        value = config_df[config_df['type'] == type]

        config = pdfkit.configuration(wkhtmltopdf=value['value'].values[0])

        # Use output_text instead of html_text in the following line
        invoice_file_name = f"{self.INVOICE_PATH}/{bill_no.replace('/', '_')}_{client_name}.pdf"
        pdfkit.from_string(output_text, invoice_file_name, configuration=config)

        messagebox.showinfo("Invoice Generated", "Invoice generated successfully!")
        self.clear_datas()


    def create_invoice_pdf_v1(self):
        customer_details = {
            "Name": self.client_name_var.get(),
            "Bill No.": self.bill_label.get(),
            "Bill Date": self.calendar.get_date(),
            "State": "33-Tamil Nadu",
            "GSTN": ""
        }
        price_variable = self.total_cost_var.get()
        tax_value = round(price_variable * 0.05, 2)
        total_value = price_variable + tax_value

        invoice_items = [
            ["S. No.", "Particulars", "Amount"],
            [1, self.pattern_var.get(), price_variable]
        ]

        tax_details = [
            ["Taxable Value", price_variable],
            # ["CGST @ 2.50%", "169.56"],
            # ["SGST @ 2.50%", "169.56"],
            ["IGST @ 5.00%", tax_value],
            ["Invoice Value", total_value],
            ["Amount Receivable", math.floor(total_value)]
        ]

        # Create a PDF document
        doc = SimpleDocTemplate("invoice.pdf", pagesize=letter)
        elements = []

        # Create a title
        styles = getSampleStyleSheet()
        title = "Tax Invoice"
        elements.append(Paragraph(title, styles["Title"]))
        elements.append(Paragraph("", styles["Normal"]))  # Add some space

        # Create customer details
        for key, value in customer_details.items():
            elements.append(Paragraph(f"<b>{key}:</b> {value}", styles["Normal"]))
        elements.append(Paragraph("<br/><br/>", styles["Normal"]))  # Add some space

        # Create a table for invoice items
        data = invoice_items
        t = Table(data, colWidths=[30, 270, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(Paragraph("Invoice Details:", styles["Heading2"]))  # Add a heading
        elements.append(t)
        elements.append(Paragraph("<br/><br/>", styles["Normal"]))  # Add some space

        # Create a table for tax details
        data = tax_details
        t = Table(data, colWidths=[300, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(Paragraph("Tax Details:", styles["Heading2"]))  # Add a heading
        elements.append(t)
        elements.append(Spacer(1, 10))  # Add some space
        elements.append(Paragraph("<br/><br/>", styles["Normal"]))  # Add some space

        centered_style = styles['Normal']

        elements.append(Paragraph("Thanks for the Order !!!", centered_style))
        # Render the PDF
        doc.build(elements)
        messagebox.showinfo("Invoice Generated", "Invoice generated successfully!")

    def show_purchase_interface(self):
        purchase_app = PurchaseInterface()
        purchase_app.root.mainloop()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        # file_menu.add_command(label="Open Purchase Entry", command=self.show_purchase_interface)
        # file_menu.add_command(label="Open Application 2", command=self.show_application2)
        # file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def save_client_details_to_json(self):
        df = pd.DataFrame(self.source_data_list)

        # Extracting the length of the DataFrame
        length_of_df = len(df)

        # Creating df1 DataFrame
        df1 = pd.DataFrame({
            'bill_no': [self.bill_label.get()] * length_of_df,
            'client_name': [self.client_name_var.get()] * length_of_df,
            'bill_date': [self.calendar.get_date()] * length_of_df
        })

        # Concatenating df1 and df horizontally
        concat_df = pd.concat([df1, df], axis=1)

        # Extracting bill_no and client_name for the file name
        bill_no = str(self.bill_label.get())
        client_name = str(self.client_name_var.get())

        details_file_name = f"{self.DETAILS_PATH}/{bill_no.replace('/', '_')}_{client_name}.xlsx"

        concat_df.to_excel(details_file_name, index=False)
        messagebox.showinfo("Bill Details Generated", "Bill generated successfully!")

    def generate_save_details(self):
        add_layer_button = tk.Button(self.root, text="Save Details", command=self.save_client_details_to_json)
        add_layer_button.grid(row=1, column=6, columnspan=2, padx=3, pady=3)
        add_layer_button.config(font=("times new roman", 12))

    def refresh_datas(self):
        refresh_button = tk.Button(self.root, text="Refresh", command=self.load_excel_datas)
        refresh_button.grid(row=2, column=6, columnspan=2, padx=3, pady=3)
        refresh_button.config(font=("times new roman", 12))

    def generate_in_voice_button(self):
        add_layer_button = tk.Button(self.root, text="Generate Invoice", command=self.create_invoice_pdf)
        add_layer_button.grid(row=0, column=6, columnspan=2, padx=3, pady=3)
        add_layer_button.config(font=("times new roman", 12))

    def create_bill_info_section(self):
        self.create_label_and_entry("Bill No:")
        self.create_date_entry("Bill Date:")
        self.create_client_label_and_entry()
        self.create_dress_pattern_combobox()
        self.create_piece_box()
        self.create_machine_hours()
        self.create_embroidery_hours_default()

        self.create_dying_charges()
        self.create_machine_hours_cost()
        self.create_embroidery_material_cost()
        self.generate_machine_cost()
        self.create_embroidery_hours()
        self.create_other_cost()

        self.generate_embroidery_cost()
        self.create_fixed_cost()

        self.create_accessory_price_cost()
        self.create_total_cost()
        self.create_accessories_dropdown()

    def create_watermark(self):
        try:
            # Load your image (supported formats are GIF, PGM, PPM, and PNG)
            image = PhotoImage(file=f"{self.INPUT_IMAGES_PATH}/400PngdpiLogoCropped.png")

            # Create a Label with the image
            image_label = tk.Label(self.root, image=image)
            image_label.image = image  # Keep a reference to the PhotoImage instance
            image_label.grid(row=12, column=4, sticky="e")

            # Remove the previous label (if exists)
            total_cost_label = tk.Label(self.root, text="Aadhiraya", anchor="w", justify="left")
            total_cost_label.grid_forget()
        except Exception as e:
            print("Error:", e)

    def recalculate_total_cost(self, *args):
        # Calculate the total cost by summing up all individual costs
        # total_cost = sum([
        #     self.machine_cost_var.get() if isinstance(self.machine_cost_var.get(), int) else 0,
        #     self.embroidery_cost_var.get() if isinstance(self.embroidery_cost_var.get(), int) else 0,
        #     self.embroidery_material_cost_var.get() if isinstance(self.embroidery_material_cost_var.get(), int) else 0,
        #     self.fixed_cost_var.get() if isinstance(self.fixed_cost_var.get(), int) else 0,
        #     self.other_cost_var.get() if isinstance(self.other_cost_var.get(), int) else 0,
        #     self.dying_var.get() if isinstance(self.dying_var.get(), int) else 0,
        #     self.total_layer_cost_var.get() if isinstance(self.dying_var.get(), int) else 0,
        #     self.total_accessory_cost_var.get() if isinstance(self.total_accessory_cost_var.get(), int) else 0,
        # ])
        total_cost = 0
        for record in self.source_data_list:
            try:
                total_cost += int(record['total_cost'])
            except:
                continue

        # Update the total cost variable
        self.total_cost_var.set(total_cost)

        self.total_cost_in_word.delete("1.0", tk.END)  # Clear existing text
        self.total_cost_in_word.insert(tk.END, number_to_words(total_cost))

    # Inside the __init__ method, add the following lines to link the recalculate_total_cost function to the trace of
    # cost variables:

    # Also, update the create_total_cost method to display the total cost and add a label to display it:

    def create_total_cost(self):
        self.total_cost_var = tk.IntVar()
        total_cost_label = tk.Label(self.root, text="Total Cost", anchor="w", justify="left")
        total_cost_label.grid(row=12, column=0, padx=3, pady=3, sticky="e")
        total_cost_label.config(font=("times new roman", 14, 'bold'),
                                fg="black",
                                bd=16,
                                )  # Change text color

        total_cost_entry = tk.Entry(self.root, width=10, textvariable=self.total_cost_var, bg="lightgray",
                                    justify="right")
        total_cost_entry.grid(row=12, column=1, padx=3, pady=3, sticky="w")
        total_cost_entry.config(font=("times new roman", 14, 'bold'), fg="black",
                                relief=tk.SUNKEN)  # Change background color and border style

        self.total_cost_in_word = Text(self.root, wrap=tk.WORD, width=23, height=3,
                                       font=("times new roman", 12, 'italic'))

        self.total_cost_in_word.grid(row=12, column=2, padx=3, pady=3, sticky="w")

        self.second_right_row_number += 1

    def create_fixed_cost(self):
        self.fixed_cost_var = tk.IntVar()
        fixed_cost_label = tk.Label(self.root, text="Fixed Cost", anchor="w", justify="left")
        fixed_cost_label.grid(row=self.second_right_row_number, column=4, padx=3, pady=3, sticky="e")
        fixed_cost_label.config(font=("times new roman", 12))

        self.fixed_cost_entry = tk.Entry(self.root, width=10, textvariable=self.fixed_cost_var, justify="right")
        self.fixed_cost_entry.grid(row=self.second_right_row_number, column=5, padx=3, pady=3, sticky="e")
        self.fixed_cost_entry.config(font=("times new roman", 12))

        self.fixed_cost_var.set(0)

        self.second_right_row_number += 1

    def create_accessory_price_cost(self):
        label = tk.Label(self.root, text="Qnty:")
        label.grid(row=self.second_right_row_number, column=4, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.accessory_quantity_var = tk.IntVar()
        self.accessory_quantity_entry = tk.Spinbox(self.root, textvariable=self.accessory_quantity_var, from_=0,
                                                   to=1000, width=5)
        self.accessory_quantity_entry.grid(row=self.second_right_row_number, column=5, padx=3, pady=3, sticky="e")
        self.accessory_quantity_entry.config(font=("times new roman", 12))

        self.second_right_row_number += 1

        label = tk.Label(self.root, text="Price:")
        label.grid(row=self.second_right_row_number, column=4, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.accessory_price_var = tk.IntVar()
        self.price_entry = tk.Entry(self.root, textvariable=self.accessory_price_var,
                                    width=10)  # Change to Entry widget
        self.price_entry.grid(row=self.second_right_row_number, column=5, padx=3, pady=3, sticky="e")
        self.price_entry.config(font=("times new roman", 12))  # Apply the same font style

        # self.accessory_quantity_var.trace("w", self.update_accessory_price)

        self.second_right_row_number += 1

    def reload_accessory_dropdown(self):
        stock_df = self.stock_df.loc[(self.stock_df['S. No.'] >= 200) & (~self.stock_df['Name of Item'].isna())]
        new_options = list(stock_df['Name of Item'].values)
        new_options.sort()
        if len(new_options) == len(self.accessories_items):
            return
        # Clear existing options and set new options
        self.accessories_items.clear()
        self.accessories_items.extend(new_options)

        # Set the dropdown to the first item in the new options
        if self.accessories_items:
            self.accessory_var.set(self.accessories_items[0])

        # Configure the dropdown to use the updated options
        self.accessory_layer_dropdown["values"] = self.accessories_items

    def create_accessories_dropdown(self):

        stock_df = self.stock_df.loc[(self.stock_df['S. No.'] >= 200) & (~self.stock_df['Name of Item'].isna())]
        self.accessories_items = list(stock_df['Name of Item'].values)
        self.accessories_items.sort()

        label = tk.Label(self.root, text="Accessories:", anchor="w", justify="left")
        label.grid(row=self.right_row_number, column=2, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.accessory_var = tk.StringVar()
        self.accessory_layer_dropdown = ttk.Combobox(self.root, textvariable=self.accessory_var,
                                                     values=self.accessories_items,
                                                     state='readonly', justify='center')
        self.accessory_var.set(self.accessories_items[0])
        self.accessory_layer_dropdown.grid(row=self.right_row_number, column=3, padx=3, pady=3, sticky="e")
        self.accessory_layer_dropdown.config(font=("times new roman", 12))

        self.right_row_number += 1

    def create_other_cost(self):
        self.other_cost_var = tk.IntVar()
        other_cost_label = tk.Label(self.root, text="Other Cost", anchor="w", justify="left")
        other_cost_label.grid(row=self.right_row_number, column=2, padx=3, pady=3, sticky="e")
        other_cost_label.config(font=("times new roman", 12))

        self.other_cost_entry = tk.Entry(self.root, width=10, textvariable=self.other_cost_var, justify="right")
        self.other_cost_entry.grid(row=self.right_row_number, column=3, padx=3, pady=3, sticky="e")
        self.other_cost_entry.config(font=("times new roman", 12))

        self.other_cost_var.set(0)

        self.right_row_number += 1

    def create_embroidery_material_cost(self):
        self.embroidery_material_cost_var = tk.IntVar()
        embroidery_material_cost_label = tk.Label(self.root, text="Embroidery Material Cost", anchor="w",
                                                  justify="left")
        embroidery_material_cost_label.grid(row=self.second_right_row_number, column=4, padx=3, pady=3, sticky="e")
        embroidery_material_cost_label.config(font=("times new roman", 12))

        self.embroidery_material_cost_entry = tk.Entry(self.root, width=10,
                                                       textvariable=self.embroidery_material_cost_var,
                                                       justify="right")
        self.embroidery_material_cost_entry.grid(row=self.second_right_row_number, column=5, padx=3, pady=3, sticky="e")
        self.embroidery_material_cost_entry.config(font=("times new roman", 12))

        self.embroidery_material_cost_var.set(0)

        self.second_right_row_number += 1

    def update_embroidery_cost(self, *args):
        try:
            quantity = self.embroidery_in_hrs_var.get() if isinstance(self.embroidery_in_hrs_var.get(), int) else 0
            if isinstance(quantity, int):
                price = self.embroidery_in_hrs_var.get() * self.embroidery_var.get()
                self.embroidery_cost_var.set(price)
            else:
                self.embroidery_in_hrs_var.set(0)
        except ValueError:
            self.embroidery_in_hrs_var.set(0)

    def generate_embroidery_cost(self):
        self.embroidery_cost_var = tk.IntVar()
        embroidery_cost_label = tk.Label(self.root, text="Embroidery cost", anchor="w", justify="left")
        embroidery_cost_label.grid(row=self.second_right_row_number, column=4, padx=3, pady=3, sticky="e")
        embroidery_cost_label.config(font=("times new roman", 12))

        self.embroidery_cost_entry = tk.Entry(self.root, width=10, textvariable=self.embroidery_cost_var,
                                              justify="right")
        self.embroidery_cost_entry.grid(row=self.second_right_row_number, column=5, padx=3, pady=3, sticky="e")
        self.embroidery_cost_entry.config(font=("times new roman", 12))

        self.embroidery_cost_var.set(0)

        self.embroidery_in_hrs_var.trace("w", self.update_embroidery_cost)
        self.second_right_row_number += 1

    def create_embroidery_hours(self):
        self.embroidery_in_hrs_var = tk.DoubleVar()
        embroidery_in_hrs_label = tk.Label(self.root, text="Embroidery Manhours", anchor="w", justify="left")
        embroidery_in_hrs_label.grid(row=self.right_row_number, column=2, padx=3, pady=3, sticky="e")
        embroidery_in_hrs_label.config(font=("times new roman", 12))

        self.embroidery_in_hrs_entry = tk.Spinbox(self.root, width=5, textvariable=self.embroidery_in_hrs_var, from_=0,
                                                  to=1000, increment=0.25  # Set the increment value for float
                                                  )
        self.embroidery_in_hrs_entry.grid(row=self.right_row_number, column=3, padx=3, pady=3, sticky="e")
        self.embroidery_in_hrs_entry.config(font=("times new roman", 12))

        self.right_row_number += 1

    def update_state(self, state):
        self.piece_entry.config(state=state)
        self.price_entry.config(state=state)
        self.dying_entry.config(state=state)
        self.machine_in_hours_entry.config(state=state)
        self.embroidery_entry.config(state=state)
        self.machine_entry.config(state=state)
        self.machine_cost_entry.config(state=state)
        self.other_cost_entry.config(state=state)
        self.embroidery_material_cost_entry.config(state=state)
        self.accessory_quantity_entry.config(state=state)
        self.embroidery_in_hrs_entry.config(state=state)
        self.add_accessory_button.config(state=state)
        self.quantity_entry.config(state=state)
        self.embroidery_cost_entry.config(state=state)

    @staticmethod
    def show_subscription_remainder(remaining_days):
        if remaining_days >= 0:
            messagebox.showinfo(
                'Subscription Expiration Reminder',
                f'Your subscription will expire in {remaining_days} days. '
                'Please renew your subscription to avoid service interruption.'
            )
        else:
            messagebox.showinfo(
                'Subscription Expiration Reminder',
                f'Your subscription will expires today at 12:00 Pm. '
                'Please renew your subscription to avoid service interruption.'
            )

    @staticmethod
    def get_expiry_date():
        dates = [2, 2, 2024]
        raw_file_url = "https://raw.githubusercontent.com/pradeepvsi7/Binary_to_decimal/main/expiry_date.txt"

        # try:
        #     # Fetch the raw content of the file
        #     response = requests.get(raw_file_url)
        #
        #     # Read and return the first line of the file
        #     lines = response.text.split('\n')
        #     if lines:
        #         return lines[0].split(',')
        #     else:
        #         return dates
        #
        # except Exception as e:
        #     print(f"Error fetching file from {raw_file_url}: {e}")
        return dates

    def check_expiration_date(self):
        day, month, year = list(map(int,self.get_expiry_date()))
        print(day, month, year)

        expiration_date = datetime.datetime.strptime(f'{year}-{month}-{day}', '%Y-%m-%d')
        current_date = datetime.datetime.now()
        remaining_days = (expiration_date - current_date).days

        if 0 <= remaining_days <= 5:
            self.show_subscription_remainder(remaining_days)
        elif datetime.datetime.now() > datetime.datetime(year, month, day, 23, 59, 59):
            messagebox.showinfo('Subscription Expired',
                                'Your Subscription has been expired please Subscribe to continue service...!')
            raise SystemExit

    def update_fixed_price(self, *args):
        pattern_dress = self.pattern_var.get()
        if self.pattern_price_hash_data.get(pattern_dress):
            self.fixed_cost_var.set(self.pattern_price_hash_data[pattern_dress])
            self.update_state('disabled')
            self.layer_var.set("")
        else:
            self.update_state('normal')
            self.layer_var.set(self.layer_options[0])
            self.fixed_cost_var.set(0)

    def update_accessory_price(self, *args):
        layer = self.layer_var.get()
        if self.layer_price_hash_data.get(layer):
            self.accessory_price_var.set(self.layer_price_hash_data[layer] * self.accessory_quantity_var.get())
        else:
            self.accessory_price_var.set(0)

    def update_layer_price(self, *args):
        layer = self.layer_var.get()
        if self.layer_price_hash_data.get(layer):
            self.price_var.set(self.layer_price_hash_data[layer] * self.quantity_var.get())
        else:
            self.price_var.set(0)

    def update_machine_cost(self, *args):
        try:
            quantity = self.machine_in_hours_var.get() if isinstance(self.machine_in_hours_var.get(), int) else 0
            if isinstance(quantity, int):
                price = self.machine_in_hours_var.get() * self.machine_hr_var.get()
                self.machine_cost_var.set(price)
            else:
                self.machine_cost_var.set(0)
        except ValueError:
            self.machine_cost_var.set(0)

    def generate_machine_cost(self):
        self.machine_cost_var = tk.IntVar()
        machine_cost_label = tk.Label(self.root, text="Machine Cost", anchor="w", justify="left")
        machine_cost_label.grid(row=self.second_right_row_number, column=4, padx=3, pady=3, sticky="e")
        machine_cost_label.config(font=("times new roman", 12))

        self.machine_cost_entry = tk.Entry(self.root, width=10, textvariable=self.machine_cost_var, justify="right")
        self.machine_cost_entry.grid(row=self.second_right_row_number, column=5, padx=3, pady=3, sticky="e")
        self.machine_cost_entry.config(font=("times new roman", 12))

        self.machine_cost_var.set(0)

        self.machine_in_hours_var.trace("w", self.update_machine_cost)
        self.second_right_row_number += 1

    def create_machine_hours_cost(self):
        self.machine_in_hours_var = tk.DoubleVar()
        machine_in_hours_label = tk.Label(self.root, text="Machine Hrs", anchor="w", justify="left")
        machine_in_hours_label.grid(row=self.right_row_number, column=2, padx=3, pady=3, sticky="e")
        machine_in_hours_label.config(font=("times new roman", 12))

        self.machine_in_hours_entry = tk.Spinbox(self.root, width=5, textvariable=self.machine_in_hours_var, from_=0,
                                                 to=1000, increment=0.25)
        self.machine_in_hours_entry.grid(row=self.right_row_number, column=3, padx=3, pady=3, sticky="e")
        self.machine_in_hours_entry.config(font=("times new roman", 12))

        self.right_row_number += 1

    def create_dying_charges(self):
        self.second_right_row_number += 1
        self.dying_var = tk.IntVar()
        dying_label = tk.Label(self.root, text="Dying charges", anchor="w", justify="left")
        dying_label.grid(row=self.second_right_row_number, column=4, padx=3, pady=3, sticky="e")
        dying_label.config(font=("times new roman", 12))

        self.dying_entry = tk.Entry(self.root, width=10, textvariable=self.dying_var, justify="right")
        self.dying_entry.grid(row=self.second_right_row_number, column=5, padx=3, pady=3, sticky="e")
        self.dying_entry.config(font=("times new roman", 12))

        self.dying_var.set(0)

        self.second_right_row_number += 1

    def create_embroidery_hours_default(self):
        self.embroidery_var = tk.IntVar()
        embroidery_label = tk.Label(self.root, text="Embroidery labour Cost/Hour", anchor="w", justify="left")
        embroidery_label.grid(row=self.right_row_number, column=2, padx=3, pady=3, sticky="e")
        embroidery_label.config(font=("times new roman", 12))

        self.embroidery_entry = tk.Entry(self.root, width=10, textvariable=self.embroidery_var, justify="right")
        self.embroidery_entry.grid(row=self.right_row_number, column=3, padx=3, pady=3, sticky="e")
        self.embroidery_entry.config(font=("times new roman", 12))

        self.embroidery_var.set(550)
        self.right_row_number += 1

    def create_machine_hours(self):
        self.machine_hr_var = tk.IntVar()
        machine_label = tk.Label(self.root, text="Machine labour Cost/Hour", anchor="w", justify="left")
        machine_label.grid(row=self.right_row_number, column=2, padx=3, pady=3, sticky="e")
        machine_label.config(font=("times new roman", 12))

        self.machine_entry = tk.Entry(self.root, width=10, textvariable=self.machine_hr_var, justify="right")
        self.machine_entry.grid(row=self.right_row_number, column=3, padx=3, pady=3, sticky="e")
        self.machine_entry.config(font=("times new roman", 12))

        # Set the initial/default value for the Entry
        self.machine_hr_var.set(750)
        self.right_row_number += 1

    def reload_client_names_dropdown(self):
        df = self.client_df.loc[~self.client_df['Client Names'].isna()]
        new_options = list(df['Client Names'].values)
        new_options.sort()
        if len(new_options) == len(self.client_names):
            return
        # Clear existing options and set new options
        self.client_names.clear()
        self.client_names.extend(new_options)

        # Set the dropdown to the first item in the new options
        if self.client_names:
            self.client_name_var.set(self.client_names[0])

        # Configure the dropdown to use the updated options
        self.client_name_combobox["values"] = self.client_names

    def create_client_label_and_entry(self):
        df = self.client_df.loc[~self.client_df['Client Names'].isna()]

        self.client_names = list(df['Client Names'].values)
        self.client_names.sort()

        label = tk.Label(self.root, text='Client Name:', anchor="w", justify="left")
        label.grid(row=0, column=4, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.client_name_var = tk.StringVar()
        self.client_name_combobox = ttk.Combobox(self.root, textvariable=self.client_name_var, values=self.client_names,
                                                 state="readonly")
        self.client_name_combobox.set(self.client_names[0])
        self.client_name_combobox.grid(row=0, column=5, padx=3, pady=3, sticky="e")
        self.client_name_combobox.config(font=("times new roman", 12))
        # self.second_right_row_number += 1

    def create_label_and_entry(self, label_text):
        self.bill_label = tk.StringVar()
        label = tk.Label(self.root, text=label_text, anchor="w", justify="left")
        label.grid(row=self.row_number, column=0, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.bill_entry = tk.Entry(self.root, width=20, justify="center", textvariable=self.bill_label)
        self.bill_entry.grid(row=self.row_number, column=1, padx=3, pady=3, sticky="e")
        self.bill_entry.config(font=("times new roman", 12, 'bold'))
        self.row_number += 1

    def create_date_entry(self, label_text):
        label = tk.Label(self.root, text=label_text, anchor="w", justify="left")
        label.grid(row=self.right_row_number, column=2, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.calendar = DateEntry(self.root, width=17, background="darkblue",
                                  foreground="white", borderwidth=2, date_pattern="dd/mm/yyyy")
        self.calendar.grid(row=self.right_row_number, column=3, padx=3, pady=3, sticky="e")
        self.calendar.config(font=("times new roman", 12))
        self.right_row_number += 1

    def update_layer_prices_hash_map(self, df):
        for row in df.iterrows():
            data_dict = row[1].to_dict()
            piece_rate = data_dict['Selling Price of Material / Mtr']
            if not pd.isna(piece_rate) and piece_rate != '-':
                self.layer_price_hash_data[data_dict['Name of Item']] = piece_rate

    def update_piece_prices_hash_map(self, df):
        for row in df.iterrows():
            data_dict = row[1].to_dict()
            piece_rate = data_dict['Rate/ Piece']
            if not pd.isna(piece_rate):
                self.pattern_price_hash_data[data_dict['Dress Patterns']] = piece_rate

    def reload_dress_pattern_dropdown(self):
        df = self.data_df.loc[~self.data_df['Dress Patterns'].isna()]
        new_options = list(df['Dress Patterns'].values)
        new_options.sort()
        if len(new_options) == len(self.dress_pattern_values):
            return
        # Clear existing options and set new options
        self.dress_pattern_values.clear()
        self.dress_pattern_values.extend(new_options)

        # Set the dropdown to the first item in the new options
        if self.dress_pattern_values:
            self.pattern_var.set(self.dress_pattern_values[0])

        # Configure the dropdown to use the updated options
        self.dress_pattern_combobox["values"] = self.dress_pattern_values

    def create_dress_pattern_combobox(self):
        self.row_number += 1
        label = tk.Label(self.root, text="Dress Pattern:", anchor="w", justify="left")
        label.grid(row=self.row_number, column=0, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        df = self.data_df.loc[~self.data_df['Dress Patterns'].isna()]

        self.dress_pattern_values = list(df['Dress Patterns'].values)
        self.dress_pattern_values.sort()

        self.pattern_var = tk.StringVar()
        self.dress_pattern_combobox = ttk.Combobox(self.root, textvariable=self.pattern_var,
                                                   values=self.dress_pattern_values,
                                                   state="readonly")
        self.dress_pattern_combobox.set(self.dress_pattern_values[0])
        self.dress_pattern_combobox.grid(row=self.row_number, column=1, padx=3, pady=3, sticky="e")
        self.dress_pattern_combobox.config(font=("times new roman", 12))

        self.pattern_var.trace("w", self.update_fixed_price)
        self.row_number += 1

    def create_piece_box(self):
        self.piece_var = tk.StringVar()
        piece_label = tk.Label(self.root, text="Enter Piece Name", anchor="w", justify="left")
        piece_label.grid(row=self.row_number, column=0, padx=3, pady=3, sticky="e")
        piece_label.config(font=("times new roman", 12))

        self.piece_entry = tk.Entry(self.root, width=20, textvariable=self.piece_var, justify="right")
        self.piece_entry.grid(row=self.row_number, column=1, padx=3, pady=3, sticky="e")
        self.piece_entry.config(font=("times new roman", 12))

        self.piece_var.set("")
        self.row_number += 1

    def create_layer_input(self):
        self.create_dropdown_layer()
        self.create_numeric_quantity()
        self.create_calculated_price()

    def reload_layer_dropdown(self):
        stock_df = self.stock_df[(self.stock_df['S. No.'] <= 200) & (~self.stock_df['Name of Item'].isna())]
        new_options = list(stock_df['Name of Item'].values)
        new_options.sort()
        if len(new_options) == len(self.layer_options):
            return

        # Clear existing options and set new options
        self.layer_options.clear()
        self.layer_options.extend(new_options)

        # Set the dropdown to the first item in the new options
        if self.layer_options:
            self.layer_var.set(self.layer_options[0])

        # Configure the dropdown to use the updated options
        self.layer_dropdown["values"] = self.layer_options

    def create_dropdown_layer(self):

        stock_df = self.stock_df[(self.stock_df['S. No.'] <= 200) & (~self.stock_df['Name of Item'].isna())]
        self.layer_options = list(stock_df['Name of Item'].values)
        self.layer_options.sort()

        label = tk.Label(self.root, text="Layer:", anchor="w", justify="left")
        label.grid(row=self.row_number, column=0, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.layer_var = tk.StringVar()
        self.layer_dropdown = ttk.Combobox(self.root, textvariable=self.layer_var, values=self.layer_options,
                                           state='readonly')

        self.layer_var.set(self.layer_options[0])
        self.layer_dropdown.grid(row=self.row_number, column=1, padx=3, pady=3, sticky="e")
        self.layer_dropdown.config(font=("times new roman", 12))

        self.row_number += 1

    def create_numeric_quantity(self):
        label = tk.Label(self.root, text="Quantity:", anchor="w", justify="left")
        label.grid(row=self.row_number, column=0, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.quantity_var = tk.DoubleVar()
        self.quantity_entry = tk.Spinbox(self.root, textvariable=self.quantity_var, from_=0, to=1000, width=6,
                                         increment=0.1)
        self.quantity_entry.grid(row=self.row_number, column=1, padx=3, pady=3, sticky="e")
        self.quantity_entry.config(font=("times new roman", 12))
        self.row_number += 1

        self.quantity_var.trace('w', self.update_layer_price)

    def create_calculated_price(self):
        label = tk.Label(self.root, text="Price:", anchor="w", justify="left")
        label.grid(row=self.row_number, column=0, padx=3, pady=3, sticky="e")
        label.config(font=("times new roman", 12))

        self.price_var = tk.IntVar()
        price_entry = tk.Entry(self.root, textvariable=self.price_var, justify="right",
                               width=10)  # Change to Entry widget
        price_entry.grid(row=self.row_number, column=1, padx=3, pady=3, sticky="e")
        price_entry.config(font=("times new roman", 12))  # Apply the same font style
        self.row_number += 1

        self.quantity_var.trace("w", self.update_layer_price)
        self.layer_var.trace("w", self.update_layer_price)

    def add_accessory(self):
        # self.update_accessory_cost()
        accessory = self.accessory_var.get()
        quantity = self.accessory_quantity_var.get()
        price = self.accessory_price_var.get()
        layer_data = (accessory, quantity, price)

        dress_name = self.pattern_var.get()
        piece_name = self.piece_var.get()
        layer_name = self.layer_var.get()
        self.tuple_key = (dress_name, piece_name, layer_name)
        if self.tuple_key in self.accessory_data_dict:
            self.accessory_data_dict[self.tuple_key].append(layer_data)
        else:
            self.accessory_data_dict[self.tuple_key] = [layer_data]

        self.accessory_listbox.insert("", "end", values=layer_data)

        delete_button = tk.Button(self.root, text="Delete Acrs.", command=self.delete_accessory)
        delete_button.grid(row=self.row_number, column=3, padx=3, pady=3, columnspan=2)
        delete_button.config(
            font=("times new roman", 12),
            bg="red",  # Background color
            fg="white",  # Text color
            relief=tk.RAISED,  # Raised button style
            width=10,  # Set the width of the button
            borderwidth=2,  # Border width
        )

    def create_add_accessories_button(self):
        self.add_accessory_button = tk.Button(self.root, text="Add Accessory", command=self.add_accessory)
        self.add_accessory_button.grid(row=self.row_number, columnspan=2, padx=3, pady=3, column=2)
        self.add_accessory_button.config(font=("times new roman", 12))

    def create_add_layer_button(self):
        self.add_layer_button = tk.Button(self.root, text="Add Layer", command=self.add_layer)
        self.add_layer_button.grid(row=self.row_number, columnspan=2, padx=3, pady=3, column=0)
        self.add_layer_button.config(font=("times new roman", 12))

    def create_accessory_list(self):
        column_names = ["Accessory", "Quantity", "Price"]

        self.accessory_listbox = ttk.Treeview(self.root, columns=tuple(column_names), show='headings')

        # Configure column headings
        for i, column_name in enumerate(column_names):
            self.accessory_listbox.heading(column_name, text=column_name)
            if column_name in ['Quantity', 'Price']:
                self.accessory_listbox.column(column_name, width=60, anchor='center')  # Adjust the width as needed
            else:
                self.accessory_listbox.column(column_name, width=80, anchor='center')

        # Configure the Treeview widget to span the entire first column
        self.accessory_listbox.grid(row=self.row_number + 3, column=3, columnspan=2, padx=3, pady=3, sticky='nsew')

    def create_layer_list(self):
        column_names = ["Dress Pattern", "Piece", "Layer", "Total Cost"]  # , "Quantity", "Piece Price"

        self.treeview = ttk.Treeview(root, columns=column_names, show='headings')

        # Configure column headings
        for i, column_name in enumerate(column_names):
            self.treeview.heading(column_name, text=column_name)
            if column_name in ['Quantity', 'Piece Price']:
                self.treeview.column(column_name, width=60, anchor='center')  # Adjust the width as needed
            else:
                self.treeview.column(column_name, width=80, anchor='center')

        self.treeview.grid(row=self.row_number + 3, column=0, columnspan=3, padx=3, pady=3, sticky='nsew')
        self.treeview.bind("<Double-1>", self.show_record_popup)

        # Configure the Treeview widget to span the entire first column

    def show_record_popup(self, event):
        if self.is_popped_up:
            return
        selected_item = self.treeview.selection()
        if selected_item:
            # Get the record associated with the selected item
            index = int(self.treeview.index(selected_item[0]))
            selected_record = self.source_data_list[index]

            # Open the Record Editor Popup
            RecordEditorPopup(self.root, selected_record, self.on_popup_closed)
            self.is_popped_up = True

    def on_popup_closed(self, updated_record):
        self.is_popped_up = False
        if updated_record is not None:
            # Update the Treeview with the modified record
            selected_item = self.treeview.selection()
            index = int(self.treeview.index(selected_item[0]))
            self.treeview.item(selected_item, values=updated_record)

            # Replace the existing record with the updated one
            self.source_data_list[index] = {key: value for key, value in zip(self.invoice_data_fields, updated_record)}
            self.recalculate_total_cost()

    @staticmethod
    def clear_treeview(tree_view_obj):
        for item_id in tree_view_obj.get_children():
            tree_view_obj.delete(item_id)

    def add_datas_to_tuples(self):
        self.invoice_data_fields = ['dress_pattern', 'piece_name', 'layer_name', 'total_cost',
                                    'layer_qnty', 'layer_price', 'machine_hours', 'machine_cost',
                                    'embroidery_hours', 'embroidery_cost', 'embroidery_material_cost', 'dying_charges',
                                    'other_cost', 'fixed_cost', 'accessories']
        # bill_no = self.bill_label.get()
        # client_name = self.client_name_var.get()
        # bill_date = self.calendar.get_date()
        piece_name = self.piece_var.get()
        dress_pattern = self.pattern_var.get()
        layer_name = self.layer_var.get()
        layer_qnty = self.quantity_var.get()
        layer_price = self.price_var.get()
        machine_hours = self.machine_in_hours_var.get()
        machine_cost = self.machine_cost_var.get()

        embroidery_hours = self.embroidery_in_hrs_var.get()
        embroidery_cost = self.embroidery_cost_var.get()

        embroidery_material_cost = self.embroidery_material_cost_var.get()
        dying_charges = self.dying_var.get()
        other_cost = self.other_cost_var.get()
        fixed_cost = self.fixed_cost_var.get()
        # accessory_name = self.accessory_var.get()
        # accessory_qnty = self.accessory_quantity_var.get()
        # accessory_price = self.accessory_price_var.get()
        self.piece_cost_sum = 0

        default_clear_fields = [self.piece_var, self.price_var, self.machine_cost_var, self.embroidery_cost_var,
                                self.embroidery_material_cost_var, self.dying_var, self.other_cost_var,
                                self.fixed_cost_var, self.accessory_price_var]
        seq = 1
        for field in default_clear_fields:
            if seq not in [1, 9]:
                try:
                    value_data = float(field.get())
                except Exception as e:
                    print(e)
                    value_data = 0
                self.piece_cost_sum += value_data
            if seq == 1:
                field.set("")
            else:
                field.set(0)

            seq += 1
        tuple_key = (dress_pattern, piece_name, layer_name)
        for accessory_price_value in self.accessory_data_dict.get(tuple_key, []):
            self.piece_cost_sum += accessory_price_value[-1]
        tuple_values = (dress_pattern, piece_name, layer_name, self.piece_cost_sum,
                        layer_qnty, layer_price, machine_hours, machine_cost, embroidery_hours, embroidery_cost,
                        embroidery_material_cost, dying_charges, other_cost, fixed_cost,
                        self.accessory_data_dict.get(tuple_key, tuple()))

        data_dict = {}
        for key, value in zip(self.invoice_data_fields, tuple_values):
            data_dict[key] = value

        self.source_data_list.append(data_dict)
        self.clear_treeview(self.accessory_listbox)

    def update_treeview(self):
        # Clear existing items in the Treeview
        self.treeview.delete(*self.treeview.get_children())

        dress_pattern = self.pattern_var.get()
        piece = self.piece_var.get()
        layer = self.layer_var.get()
        quantity = self.quantity_var.get()

        layer_data = (dress_pattern, piece, layer, quantity, self.piece_cost_sum)

        for item in self.source_data_list:
            self.treeview.insert("", "end", values=item)

    def add_layer(self):
        # self.update_layer_cost()
        dress_pattern = self.pattern_var.get()
        piece = self.piece_var.get()
        layer = self.layer_var.get()
        piece_price = self.price_var.get()
        quantity = self.quantity_var.get()

        self.add_datas_to_tuples()
        layer_data = (dress_pattern, piece, layer, self.piece_cost_sum, quantity, piece_price)
        self.treeview.insert("", "end", values=layer_data[:4])

        delete_button = tk.Button(self.root, text="Delete Layer", command=self.delete_layer)
        delete_button.grid(row=self.row_number, column=1, padx=3, pady=3, columnspan=2)
        delete_button.config(
            font=("times new roman", 12),
            bg="red",  # Background color
            fg="white",  # Text color
            relief=tk.RAISED,  # Raised button style
            width=10,  # Set the width of the button
            borderwidth=2,  # Border width
        )
        self.recalculate_total_cost()

    def delete_accessory(self):
        selected_index = self.accessory_listbox.selection()
        if selected_index:
            price = 0
            for item in selected_index:
                values = self.accessory_listbox.item(item, "values")
                if self.tuple_key in self.accessory_data_dict and values in self.accessory_data_dict[self.tuple_key]:
                    self.accessory_data_dict[self.tuple_key].remove(values)
                if values:
                    price += int(values[2])  # Assuming "Price" is the 4th column (0-based index)
                self.accessory_listbox.delete(item)

            # Subtract the total selected layer prices from the total layer cost
            # final_layer_cost = self.total_accessory_cost_var.get() - price
            # final_layer_cost = final_layer_cost if final_layer_cost >= 0 else 0
            # self.total_accessory_cost_var.set(final_layer_cost)

        self.accessory_quantity_var.set(0)  # Reset the quantity field

    def delete_layer(self):
        selected_index = self.treeview.selection()
        if selected_index:
            for item in selected_index:
                values = self.treeview.item(item, "values")
                self.treeview.delete(item)
                for index, data in enumerate(self.source_data_list):
                    if (data['dress_pattern'], data['piece_name'], data['layer_name']) == values[:3]:
                        self.source_data_list.pop(index)
                        break

        self.quantity_var.set(0)  # Reset the quantity field
        self.recalculate_total_cost()

    def create_total_cost_for_accessories(self):
        self.total_accessory_cost_var = tk.IntVar(value=0)  # Initialize with zero
        total_layer_cost_label = tk.Label(self.root, text="Total Accessory Cost", anchor="w", justify="left")
        total_layer_cost_label.grid(row=12, column=3, padx=3, pady=3, sticky="e", columnspan=1)
        total_layer_cost_label.config(font=("times new roman", 14, 'bold'),
                                      fg="black",
                                      bd=16,
                                      )  # Change text color

        total_layer_cost_entry = tk.Entry(self.root, width=10, textvariable=self.total_accessory_cost_var,
                                          bg="lightgray",
                                          justify="right")
        total_layer_cost_entry.grid(row=12, column=4, padx=3, pady=3, sticky="e", columnspan=1)
        total_layer_cost_entry.config(font=("times new roman", 14, 'bold'), fg="black",
                                      relief=tk.SUNKEN)  # Change background color and border style

    def create_total_cost_for_layers(self):
        self.total_layer_cost_var = tk.IntVar(value=0)  # Initialize with zero
        total_layer_cost_label = tk.Label(self.root, text="Total Layer Cost", anchor="w", justify="left")
        total_layer_cost_label.grid(row=12, column=0, padx=3, pady=3, sticky="e")
        total_layer_cost_label.config(font=("times new roman", 14, 'bold'),
                                      fg="black",
                                      bd=16,
                                      )  # Change text color

        total_layer_cost_entry = tk.Entry(self.root, width=10, textvariable=self.total_layer_cost_var, bg="lightgray",
                                          justify="right")
        total_layer_cost_entry.grid(row=12, column=1, padx=3, pady=3, sticky="e")
        total_layer_cost_entry.config(font=("times new roman", 14, 'bold'), fg="black",
                                      relief=tk.SUNKEN)  # Change background color and border style

    def update_layer_cost(self, *args):
        value_price = self.price_var.get() if isinstance(self.price_var.get(), int) else 0
        self.total_layer_cost_var.set(value_price + self.total_layer_cost_var.get())

    def update_accessory_cost(self, *args):
        value_price = self.accessory_price_var.get() if isinstance(self.accessory_price_var.get(), int) else 0
        self.total_accessory_cost_var.set(value_price + self.total_accessory_cost_var.get())

    def run(self):
        # Increase the overall window size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate the desired window size based on a percentage of the screen size (e.g., 80%)
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)

        # Set the window size
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.mainloop()


if __name__ == '__main__':
    root = tk.Tk()
    app = BillInformationApp(root)
    app.run()
