import frappe
from frappe import _

def execute():
    try:
        print("Change MwSt Accounts")
        artikelsteuervorlagen = [
            ['7.7%', '8.1%'],
            ['2.5%', '2.6%']
        ]
        ertragskonten = [
            ['3010.35 - Inserateertrag M+W MV35 - mp', '3010.37 - Inserateertrag M+W MV37 - mp'],
            ['3010.59 - Inserateertrag M+W MV59 - mp', '3010.62 - Inserateertrag M+W MV62 - mp'],
            ['3110.12 - Ertrag Einbände mp MV12 - mp', '3110.13 - Ertrag Einbände mp MV13 - mp'],
            ['3110.20 - Ertrag Einbände Einbanddecken mp MV20 - mp', '3110.21 - Ertrag Einbände Einbanddecken mp MV21 - mp'],
            ['3200.59 - Ertrag Kurse und Seminare mpS mp à la carte MV59 - mp', '3200.62 - Ertrag Kurse und Seminare mpS mp à la carte MV62 - mp'],
            ['3300.35 - Ertrag Formulare & Verträge, Versandkosten 3.5% MV35 - mp', '3300.37 - Ertrag Formulare & Verträge, Versandkosten 3.7% MV37 - mp'],
            ['3300.59 - Ertrag Formulare & Broschüren 5.9% MV59 - mp', '3300.62 - Ertrag Formulare & Broschüren 6.2% MV62 - mp'],
            ['3320.20 - Ertrag kant. Formulare & Verträge 2.0% MV20 - mp', '3320.21 - Ertrag kant. Formulare & Verträge 2.1% MV21 - mp'],
            ['3601.35 - Ertrag Dienstleistungen GS an Sektionen MV35 - mp', '3601.37 - Ertrag Dienstleistungen GS an Sektionen MV37 - mp'],
            ['3601.59 - Ertrag Dienstleistungen GS an Sektionen MV59 - mp', '3601.62 - Ertrag Dienstleistungen GS an Sektionen MV62 - mp'],
            ['3610.35 - Übriger Ertrag GS MV35 - mp', '3610.37 - Übriger Ertrag GS MV37 - mp'],
            ['3610.59 - Übriger Ertrag GS MV59 - mp', '3610.62 - Übriger Ertrag GS MV62 - mp']
        ]
        
        for artikelsteuervorlage in artikelsteuervorlagen:
            update = frappe.db.sql("""UPDATE `tabItem Tax` SET `item_tax_template` = '{neu}' WHERE `item_tax_template` = '{alt}'""".format(neu=artikelsteuervorlage[1], alt=artikelsteuervorlage[0]), as_list=True)
            frappe.db.commit()
        for ertragskonto in ertragskonten:
            update = frappe.db.sql("""UPDATE `tabItem Default` SET `income_account` = '{neu}' WHERE `income_account` = '{alt}'""".format(neu=ertragskonto[1], alt=ertragskonto[0]), as_list=True)
            frappe.db.commit()
        print("Done")
    except Exception as err:
        print("Patch v1.11.0 failed")
        print(str(err))
        pass
    return