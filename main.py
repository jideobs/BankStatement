import re
import argparse
import csv

import PyPDF2


class BankStatement(object):
    TRANSACTION_TYPE_CREDIT = 'CREDIT'
    TRANSACTION_TYPE_DEBIT = 'DEBIT'

    def __init__(self, pdfpath, opening_balance, row_separator=None, password=None):
        self.columns = []
        self.row_separator = row_separator        
        self.opening_balance = opening_balance

        self.pdf_reader = self.read_pdf(pdfpath)
        self.decrypt_pdf_file(password)

    def read_pdf(self, pdfpath):
        pdf_file_obj = open(pdfpath, 'rb')
        pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)
        return pdf_reader

    def decrypt_pdf_file(self, password):
        if not self.pdf_reader.isEncrypted:
            return

        if password is None:
            raise Exception('PDF is encrypted and password is not provided.')
        
        if not self.pdf_reader.decrypt(password):
            raise Exception('Could not decrypt file check password.')

    def get_row_transaction_date(self, row):
        raise NotImplemented('Must be implemented.')

    def get_row_balance(self, row):
        raise NotImplemented('Must be implemented.')
    
    def get_row_transaction_amount(self, row):
        raise NotImplemented('Must be implemented.')

    def get_narration(self, row):
        raise NotImplemented('Must be implemented.')

    def determine_amount_type(self, amount, previous_balance, current_balance):
        return self.TRANSACTION_TYPE_DEBIT if (previous_balance - amount) == current_balance else self.TRANSACTION_TYPE_CREDIT

    def read_pages(self):
        for i in range(self.pdf_reader.getNumPages()):
            page_obj = self.pdf_reader.getPage(i)
            yield page_obj.extractText()
    
    def process_statement(self):
        previous_balance = self.opening_balance    
        for page_text in self.read_pages():
            iterator = self.row_separator.finditer(page_text)
            previous_match = None
            for current_match in iterator:
                if not previous_match:
                    previous_match = current_match
                    continue
                row = page_text[previous_match.start():current_match.start()]
                transaction_date = self.get_row_transaction_date(row)
                row_balance = self.get_row_balance(row)
                row_transaction_amount = self.get_row_transaction_amount(row)
                narration = self.get_narration(row)
                transaction_type = self.determine_amount_type(row_transaction_amount, previous_balance, row_balance)
                yield {
                    'transaction_date': transaction_date,
                    'narration': narration, 
                    'transaction_amount': row_transaction_amount, 
                    'balance': row_balance, 
                    'transaction_type': transaction_type
                }
                previous_match = current_match
                previous_balance = row_balance
                # Todo how do you get the last row?.
        else:
            pass

    def generate_csv(self):
        with open('output.csv', 'w') as csvfile:
            fieldnames = ['transaction_date', 'narration', 'transaction_amount', 'balance', 'transaction_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for statement in self.process_statement():
                writer.writerow(statement)


class Zenith(BankStatement):
    def __init__(self, pdfpath, opening_balance):
        row_separator = re.compile('[\d]{2}\/[\d]{2}\/[\d]{4}[\d]{2}\/[\d]{2}\/[\d]{4}')
        super(Zenith, self).__init__(pdfpath, opening_balance, row_separator)

    def get_row_transaction_date(self, row):
        match = re.match('[\d]{2}\/[\d]{2}\/[\d]{4}', row)
        start_index = match.start()
        end_index = match.end()
        return row[start_index:end_index]

    def get_row_balance(self, row):
        str_amount = row[(row.rfind('NGN') + 3):]
        str_amount = str_amount.replace(',', '')    
        return float(str_amount)

    def get_row_transaction_amount(self, row):
        if row.find('NGNNGN') != -1:
            start_index = row.find('NGNNGN') + 6
        elif row.find('NGNGNGN') != -1:
            start_index = row.find('NGNGNGN') + 7
        elif row.find('NGNGN') != -1:
            start_index = row.find('NGNGN') + 5
        else:
            start_index = row.find('NGN') + 3
        str_amount = row[start_index:row.rfind('NGN')]
        str_amount = str_amount.replace(',', '')

        return float(str_amount)

    def get_narration(self, row):
        start_index = re.match('[\d]{2}\/[\d]{2}\/[\d]{4}[\d]{2}\/[\d]{2}\/[\d]{4}', row).end()
        end_index = row.find('NGN')
        return row[start_index:end_index]


class GTBank(BankStatement):
    def __init__(self, pdfpath, opening_balance):
        pass

    def get_row_transaction_date(self, row):
        pass
    
    def get_row_balance(self, row):
        pass
    
    def get_row_transaction_amount(self, row):
        pass

    def get_narraion(self, row):
        pass
    

def main(pdfpath, password, opening_balance):
    bank_statement = Zenith(pdfpath, opening_balance)
    bank_statement.generate_csv()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape information from bank statements')
    parser.add_argument('pdfpath', metavar='-f', type=str, help='Enter PDF file path.')
    parser.add_argument('opening_balance', metavar='-op', type=float, help='Opening balance of bank statement.')    
    parser.add_argument('--password', metavar='-p', type=str, help='Enter optional password for Encrypted PDFs')
    args = parser.parse_args()
    main(args.pdfpath, args.password, args.opening_balance)
