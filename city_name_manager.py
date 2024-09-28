import json
import os

class CityNameManager:
    def __init__(self, json_file='data/city_name_mapping.json'):
        self.json_file = json_file
        self.name_mapping = self._load_mapping()

    def _load_mapping(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_mapping(self):
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.name_mapping, f, ensure_ascii=False, indent=4)


    def clean_name(self, name):
        if name is None:
            return None
        
        name_lower = name.lower()
        removed_digits = ''.join(char for char in name_lower if not char.isdigit())
        removed_quotes = removed_digits.replace('"', '').replace("'", '')
        removed_cedex = removed_quotes.replace('cedex', '')
        name_stripped = removed_cedex.strip()
        return name_stripped


    def get_standard_name(self, name):
        cleaned_name = self.clean_name(name)
        if cleaned_name in self.name_mapping:
            return self.name_mapping[cleaned_name]
        return cleaned_name.title()

    def add_mapping(self, variant, standard_name):
        self.name_mapping[variant.lower()] = standard_name
        self.save_mapping()

    def update_from_csv(self, csv_file):
        import csv
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)  # Skip header
            for row in reader:
                if len(row) == 2:
                    english_name = row[0].strip()
                    other_names = [name for name in row[1].split(',')]
                    for name in other_names:
                        if name is not None and name != '':
                            name = name.strip()
                            self.add_mapping(name, english_name)
        self.save_mapping()