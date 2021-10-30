# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

@frappe.whitelist()
def get_qrr_reference(reference_raw='00 00000 00000 00000 00000 0000'):
    check_digit_matrix = {
        '0': [0, 9, 4, 6, 8, 2, 7, 1, 3, 5, 0],
        '1': [9, 4, 6, 8, 2, 7, 1, 3, 5, 0, 9],
        '2': [4, 6, 8, 2, 7, 1, 3, 5, 0, 9, 8],
        '3': [6, 8, 2, 7, 1, 3, 5, 0, 9, 4, 7],
        '4': [8, 2, 7, 1, 3, 5, 0, 9, 4, 6, 6],
        '5': [2, 7, 1, 3, 5, 0, 9, 4, 6, 8, 5],
        '6': [7, 1, 3, 5, 0, 9, 4, 6, 8, 2, 4],
        '7': [1, 3, 5, 0, 9, 4, 6, 8, 2, 7, 3],
        '8': [3, 5, 0, 9, 4, 6, 8, 2, 7, 1, 2],
        '9': [5, 0, 9, 4, 6, 8, 2, 7, 1, 3, 1]
    }
    
    transfer = 0
    check_digit = 0
    reference_raw = reference_raw.replace(" ", "")
    for digit in reference_raw:
        digit = int(digit)
        transfer = int(check_digit_matrix[str(transfer)][digit])
    
    check_digit = int(check_digit_matrix[str(transfer)][10])
    
    qrr_reference_raw = reference_raw + str(check_digit)
    qrr_reference = qrr_reference_raw[:2] + " " + qrr_reference_raw[2:7] + " " + qrr_reference_raw[7:12] + " " + qrr_reference_raw[12:17] + " " + qrr_reference_raw[17:22] + " " + qrr_reference_raw[22:27]
    return qrr_reference
