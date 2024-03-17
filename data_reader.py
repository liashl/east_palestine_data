import tabula
import pandas as pd
import re
import numpy as np
from datetime import datetime
import unicodedata
import csv
from datetime import datetime

#check if an element is recognizable as datetime in the format mm/dd/yy
def is_date_1(date_string):
    try:
        pd.to_datetime(date_string, format='%m/%d/%y')
        return True
    except Exception:
        return False
    
#check if an element is recognizable as datetime in the format hh:mm
def is_date_2(date_string):
    try:
        pd.to_datetime(date_string, format='%H:%M')
        return True
    except Exception:
        return False

#strip all elements of datetime in the following formats from a list: mm/dd/yy, hh:mm
def strip_datetime(input_list):
    new_input_list = [x for x in input_list if not (is_date_1(x) or is_date_2(x))]
    return(new_input_list)

#strip the following elements from a list: 'Prepared', 'Analyzed'
#This version of the scraper ignores these data.
def strip_date_headers(input_list):
    date_words = ['Prepared','Analyzed']    
    new_input_list = [x for x in input_list if not (x in date_words)]
    return(new_input_list)

#prepare to write to CSV
column_names = [
    'client_sample_id',
    'sample_date',
    'matrix',
    'method',
    'analyte',
    'result',
    'qualifier',
    'RL',
    'MDL',
    'unit',
    'dil fac',
    'EDL']

QUALIFIERS = [
    '*+',
    'H',
    'H3',
    'J',
    'S1+',
    'F1',
    'F2',
    '*+',
    'S1-',
    'B',
    'F3',
    'HF',
    '*-',
    'I',
    '*3'
]

#write column headers to top of CSV.
#can float this after the first file is complete, in order to append data from second file.
with open('norfolk_southern_data.csv','w',newline='') as f:
    w = csv.writer(f)
    w.writerow(column_names)

#paths to two pdf files containing data
path_1 = "media/NS_East Palestine IRR_WMP_4.10.2023_Vol 2-508.pdf"
path_2 = "media/NS_East Palestine IRR_WMP_4.10.2023_Vol 3-508 (1).pdf"

#page numbers for path_1
#These are all the pages containing Client Sample Data not explicitly marked "TRIP BLANK"
#With the exception of pp. 948-1009 which contain unreadable 'preliminary data' with embossed words across the table
pages_1 = '17-62,118,140-155,192-237,298,322-367,421,456-544,628,649-660,710-778,842,863-875,908-911,1078-1108,1163-1181,1244-1310,1396-1462,1545-1574'
#doc2 pages 17-62,118,140-155,192-237,298,322-367,421,456-544,628,649-660,710-778,842,863-875,908-911,1078-1108,1163-1181,1244-1310,1396-1462,1545-1574

#page numbers for path_2
#These are all the pages containing Client Sample Data not explicitly marked "TRIP BLANK"
pages_2 = '1-16,82-87,116-129,157-178,217-230,262-287,324-339,369-372,401-420,456'
#pages 1-16,82-87,116-129,157-178,217-230,262-287,324-339,369-372,401-420,456

#function for writing data from Eurofins PDF provided by EPA/Arcadis/Norfolk Southern
#this appends data, it does not overwrite
def scrape_eurofins_pdf(path,pagenums):

    #call Tabula-Py and read multiple tables into a list of dataframes using multiple tables setting
    #Set area based on where tables were located on the PDF.
    dfs = tabula.read_pdf(path, pages=pagenums, area=[[39.3975,23.715,66.1725,587.52],[69.9975,29.07,115.1325,589.05],[116.6625, 29.835,728,587.4]], guess=True, multiple_tables=True)

    #for output during debugging, make all column names visible
    pd.set_option('display.max_columns', None)

    #print calls used to visualize data during process of writing this code
    #print(dfs[0].head(50))
    #print(dfs[1].head(50))
    #print(len(dfs))

    #set substrings used to identify sample IDs, date_collected, and matrix
    #note that currently lab sample id is not yet identified
    sample_finder = 'Client Sample ID:'
    lab_sample_finder = 'Lab Sample ID:'
    date_collected_finder = 'Date Collected:'
    matrix_info_finder = 'Matrix:'

    #TODO: DELETE IF NOT NEEDED
    #sample_ids = []
    #sample_dates = []

    #set default variable for sample of last table
    client_sample_id = ''
    last_sample = 'unk'

    #set substring used to find tables where analytes are stored. They contain the word 'Method' in headers.
    table_finder = 'Method:'

    #iterate through dataframes stored by Tabula-Py
    for d in dfs:
        #create list of table headers for each dataframe
        header_list = d.columns.tolist()

        #print calls used to visualize data during process of writing this code.
        #print(header_list)
        #check if sample_finder is in the headers of an extracted dataframe

        #set default value for boolean that identifies tables with 'Method' in the header
        data_chunk_checker = False

        #iterate through list of headers
        for header in header_list:
            #check for the presence of a client sample ID
            found = re.search(sample_finder, header)

            #handle information from tables with client sample ID (extract sample ID, date collected, matrix)
            if found:
                #strip off white space and assign to variable
                client_sample_id = header[found.end():].strip()

                #TODO: delete this if not needed
                #sample_ids.append(client_sample_id)

                #extract date_collected
                #Create a boolean mask of values within dataframe containing date_collected_finder
                d2=d.apply(lambda col: col.str.contains(date_collected_finder, na=False), axis=1)

                #flatten to values and convert to list
                d3 = d.where(d2, inplace=False).values[0].tolist()

                #filter out all nulls and other non-string values
                d4 = list(filter(lambda x: isinstance(x,str),d3))

                #when flattened list contains at least 1 value, strip off white space of first (presumably only) value
                #then assign to variable
                if len(d4) > 0:
                    #strip off "Date Collected"
                    date_collected_raw = d4[0]
                    date_collected_match = re.search(date_collected_finder, date_collected_raw)

                    #assign to variable data_collected
                    date_collected = date_collected_raw[date_collected_match.end():].strip()

                    #convert date to a standard format and assign to variable date_converted
                    date_converted = datetime.strftime(datetime.strptime(date_collected, '%m/%d/%y %H:%M'),'%m/%d/%y')
                    
                    #TODO: delete this if not needed
                    #sample_dates.append(date_converted)

                #extract matrix
                #Create a boolean mask of values within dataframe containing matrix_info_finder
                d5 = d.apply(lambda col: col.str.contains(matrix_info_finder, na=False), axis=1)

                #flatten to values and convert to list
                d6 = d.where(d5, inplace=False).values[0].tolist()

                #filter out all nulls and other non-string values
                d7 = list(filter(lambda x: isinstance(x,str),d6))

                #when flattened list contains at least 1 value, strip off white space of first (presumably only) value
                #then assign to variable
                if len(d7) > 0:
                    #strip off "Matrix:"
                    matrix_raw = d7[0]
                    matrix_match = re.search(matrix_info_finder, matrix_raw)

                    #assign to variable sample_matrix
                    sample_matrix = matrix_raw[matrix_match.end():].strip()

            #if 'Method' is in the headers, set boolean data_chunk_checker to 'True'
            data_chunk = re.search(table_finder, header)
            if data_chunk:
                data_chunk_checker = True

        #some tables with data do not have 'Method' in the header.
        #for these, double check for 'Method' or 'Method:' listed in the rows of the table
        #if 'Method' or 'Method:' found in a row, set boolean data_chunk_checker to 'True'
        if not data_chunk_checker:

            for index, row in d.iterrows():
                row_expanded = row.to_list()
                method_detected = [i for i in row_expanded if any(k in str(i) for k in ['Method:', 'Method'])]

                if method_detected != []:
                    data_chunk_checker = True

        #handle raw tables believed to contain data
        if data_chunk_checker:

            #print calls used to visualize and debug during process of writing this code
            #print("---")
            #print("client_sample_id:", client_sample_id)
            #print("last_sample:",last_sample)

            #if the client_sample_id is not the same as the last table, reset the current_method to default
            if (client_sample_id != last_sample):
                current_method = 'unknown'

            #extract and store method from headers if there is one.
            #search again for method in the headers
            for header in header_list:
                header_method_checker = re.search(table_finder, header)

                #if method is found, store it
                if header_method_checker:
                    method = header[header_method_checker.end():].strip()
                    current_method = method

                    #for method headers that contain 'Continued' remove it
                    target_string = r'\(Continued\)'
                    method_match = re.search(target_string,method)

                    if method_match:
                        current_method= method[:method_match.start()].strip()

            #iterate through rows to handle special lines
                    
            #print call used for debugging
            #print("method in header is",current_method)

            #set default variables for table mechanics
            current_header_length = 0 # Number of elements in column header containing 'Analyte'
            current_headers = []

            #add data column headers for the information we're extracting to the dataframe
            columns_to_add = ['client_sample_id','sample_date','matrix','method','analyte','result','qualifier','RL','MDL','unit','dil fac','EDL']
            d = pd.concat([d,pd.DataFrame(columns = columns_to_add)])

            #create a dictionary that will indicate the locations in the dataframe of information we're extracting
            current_assign_dict = {key: None for key in columns_to_add}

            #iterate through rows of current dataframe
            for index, row in d.iterrows():

                #write additional columns in dataframe table using variable values already extracted from headers and defaults
                d.loc[index,'client_sample_id'] = client_sample_id
                d.loc[index, 'sample_date'] = date_converted
                d.loc[index, 'matrix'] = sample_matrix
                d.loc[index, 'method'] = current_method
                d.loc[index, 'a_header'] = current_header_length

                #detect special rows
                row2 = row.to_list()

                #print call for debugging
                #print('row2 is',row2)

                detect_special = ['Client','Method','Analyte','Surrogate','Isotope', 'General', '%Recovery']
                special_detected = [i for i in row2 if any(k in str(i) for k in detect_special)]

                #split list into list of words
                #use sum() to flatten list of lists
                split_special_detected = sum([i.split(' ') for i in special_detected], [])

                #handle special rows
                if split_special_detected != []:
                    #this is a special row
                    current_header_length = 0 #will be used to filter out rows.
                    d.loc[index, 'a_header'] = current_header_length

                    #print call used for debugging
                    #print('split_special_detected is',split_special_detected)

                    #handle new sample id
                    try:
                        client_index = split_special_detected.index('Client')
                        client_sample_id = " ".join(split_special_detected[(client_index + 3):])
                        d.loc[index,'client_sample_id'] = client_sample_id

                        #print call used for debugging
                        #print("Sample is:",client_sample_id)

                    except ValueError as v:
                        pass

                    #handle methods detected mid-table
                    try: 
                        method_index = split_special_detected.index('Method:')
                        current_method = " ".join(split_special_detected[(method_index +1):])
                        d.loc[index, 'method'] = current_method

                        #print call used for debugging
                        #print('New method is:', current_method)

                    except ValueError as v:
                        pass

                    #handle General Chemistry, special case of a method detected mid-table
                    try:
                        general_index = split_special_detected.index('General')
                        current_method = "General Chemistry"
                        d.loc[index, 'method'] = "General Chemistry"
                    except ValueError as v:
                        pass
                    
                    #handle the column containing 'Analyte' which needs to be separated into several columns
                    #detect number of elements in column containing Analyte
                    try:
                        #TODO: delete this first line if not needed
                        analyte_index = split_special_detected.index('Analyte')
                        current_header_length = len(split_special_detected)
                        current_headers = strip_date_headers(split_special_detected)

                        #print call used for debugging
                        #print(current_headers)

                        #create a dictionary of index assignments for each new column in the split_special_detected list
                        #this should represent the headers currently being used in the table on PDF
                        #note that columns_to_add is assigned above prior to iterating through rows
                        assign_dict = {key: None for key in columns_to_add}

                        #flatten the values of the current dataframe row (at index 'index') to a list 
                        analyte_row = d.iloc[[index]].values.flatten().tolist()

                        #print call used for debugging
                        #print("analyte_row",analyte_row)

                        #iterate through the keys in the assign_dict
                        for key in assign_dict:

                            #TODO: delete if not needed
                            #index = None
                            #for split in split_special_detected:
                            #    if split.casefold() == key.casefold():
                            #        assign_dict[key] = ('a',split_special_detected.index(split))

                            #iterate through values in the current dataframe row.
                            #look for keys (they would be in column headers rows). may need to try to split the headers into multiple words
                            for value in analyte_row:

                                #check to see if the current value matches a key (ignoring case)
                                #if so, add its index within the row to assign_dict under the relevant key
                                #assign location using a tuple: (column index, index within split column headers = 0)
                                if str(value).casefold() == key.casefold():
                                    assign_dict[key] = (analyte_row.index(value), 0)

                                #split individual value in the row into individual words
                                cats = str(value).split()

                                #check to see if the current value of split value matches a key (ignoring case)
                                #if so, add its index within the row to assign_dict under the relevant key
                                #assign location using a tuple: (column index, index within split column headers)
                                for cat in cats:
                                    if cat.casefold() == key.casefold():
                                        assign_dict[key] = (analyte_row.index(value), cats.index(cat))

                        #make this the current_assign_dict (note this should only change when header rows change)
                        current_assign_dict = assign_dict

                    except ValueError as v:
                        pass

                #create a dictionary that will contain values we eventually write to csv
                values_dict = {key: None for key in columns_to_add}

                #print call for debugging
                #print("values dict",values_dict)

                #iterate through each key in the dictionary of values
                for value_key in values_dict: 

                    #print call for debugging
                    #print(current_assign_dict)

                    #retrieve info on current length of the column of headers including 'Analyte'
                    header_length = int(d.loc[index]['a_header'])

                    #only add data for data rows (should have header values greater than zero)
                    if (header_length > 0):
                        #retrieve info using the current_assign_dict
                        if current_assign_dict[value_key] != None:

                            #print calls used in debugging
                            #print("value_key is:", value_key)
                            #print("pointer info is:", current_assign_dict[value_key])

                            #grab first part of assign_dict tuple, here labeled col_index
                            #note print call is for debugging
                            col_index = current_assign_dict[value_key][0]
                            #print("column index is", col_index)

                            #grab the cell from the current row using the col_index
                            #note print call is for debugging
                            cell_to_split = d.iloc[index][col_index]
                            #print("cell_to_split is:", cell_to_split)

                            #grab the second part of the assign_dict tuple, here labeled sub_index
                            #this is the index from a list of substrings contained in the cell
                            #note print call is for debugging
                            sub_index = current_assign_dict[value_key][1]
                            #print("sub index is:", sub_index)

                            #split the cell
                            #handle extraneous 'Analyzed' and 'Prepared' date info by removing datetime elements
                            split_cell = strip_datetime(str(cell_to_split).split())

                            #TODO: remove if possible
                            #analyte_name_length = 1 #default name length for analyte

                            #do not split cells where 'dil fac' is the key (ignoring case)
                            #note print call is for debugging
                            if (value_key.casefold() == 'dil fac'.casefold()):
                                #do not split
                                cell_val = cell_to_split
                                #print("Value for this cell is,", cell_val)
                                values_dict[value_key] = cell_val

                            #do not split cells where 'qualifier' is the key (ignoring case)
                            #there may be multiple elements
                            if (value_key.casefold() == 'qualifier'.casefold()):
                                #do not split
                                qualify_value = ''

                                #identify all the qualifiers present in this split_cell and concatenate them
                                for split in split_cell:
                                    if split in QUALIFIERS:
                                        qualify_value += split
                                        qualify_value += " "
                                
                                #assign the assembled qualifiers to values_dict, stripping off whitespace at end
                                #note print call is for debugging
                                cell_val = qualify_value.strip()
                                #print("Value for this cell is,", cell_val)
                                values_dict[value_key] = cell_val

                            #handle the first column, where 'Analyte' and other headers may be present together, in various lengths
                            elif (col_index == 0):
                                #Check if a Detect ('D') column is present in current_headers and handle missing value
                                #TODO: delete if possible
                                d_checker = False

                                if ('D' in current_headers):
                                    #TODO: delete if possible
                                    d_checker = True

                                    #print statements for debugging
                                    #print('Yes, D is present')
                                    #print(split_cell)
                                    #print(current_headers)

                                    #TODO: delete if possible
                                    #is 'D' a number or does it contain the letters 'kg' 'KG' or 'Kg'?
                                    KG_COMBOS = ['kg','KG','Kg','ug','mg']

                                    #what is the index of 'D' in current_headers
                                    d_ind = current_headers.index('D')
                                    #get the negative version of the index
                                    neg_d_ind = d_ind - len(current_headers)

                                    #is the value of split_cell at the negative index location the character '☼'
                                    #if not, insert an empty string as the value for 'D' where the column is present
                                    #print calls are for debugging
                                    try:
                                        d_ind_value = split_cell[neg_d_ind]
                                        #print(d_ind_value)

                                        if (d_ind_value == '☼'):
                                            pass
                                            #print(True)
                                        else:
                                            if (neg_d_ind == -1):
                                                split_cell.append('')
                                            else:
                                                split_cell.insert(neg_d_ind+1,'')
                                            #print(False)

                                    except IndexError as ie:
                                        print(ie)

                                    #print calls are for debugging
                                    #print(current_headers)
                                    #print('d should be empty string',split_cell)
                                    #print(d_ind)
                                    #print(neg_d_ind)

                                #handle missing MDL value when both MDL and RL are in this first header column, not separate columns
                                #Test if MDL and RL both present in current_headers but only one number in this 
                                mdl_checker = False

                                #test: MDL and RL both in current_headers?
                                #print call is for debugging
                                if all(x in current_headers for x in ['RL','MDL']):
                                    #print('yep both RL and MDL')

                                    #get position for RL
                                    #numbers expected: 2 if both RL, MDL + ND; 3 if both RL, MDL plus a numeric detect.
                                    numbers=[]
                                    nd_checker = False

                                    #is ND present / count numbers
                                    #print call is for debugging
                                    for split in split_cell:
                                        if (split == "ND"):
                                            nd_checker = True
                                        try:
                                            float(split)
                                            numbers.append(split)
                                        except ValueError as v:
                                            pass
                                    #print('array of numbers',numbers)

                                    if (nd_checker and len(numbers) <2):
                                        mdl_checker = True
                                    elif (not nd_checker and len(numbers) <3):
                                        mdl_checker = True

                                    rl_pos = current_headers.index('RL')
                                    mdl_pos = current_headers.index('MDL')

                                    #get negative position (from end of the list)
                                    end = len(current_headers)

                                    neg_pos_rl = rl_pos - end
                                    neg_pos_mdl = mdl_pos - end

                                    #print statements for debugging
                                    #try:
                                    #    float(split_cell[neg_pos_rl])
                                    #    numbers.append(split_cell[neg_pos_rl])
                                    #except ValueError as v:
                                    #    #print("RL:",v)
                                    #   mdl_checker = True

                                    #try:
                                    #   float(split_cell[neg_pos_mdl])
                                    #    numbers.append(split_cell[neg_pos_mdl])
                                    #except ValueError as v:
                                    #    #print("MDL:",v)
                                    #    mdl_checker = True

                                #if MDL is indeed missing, add an empty string in the appropriate position
                                #print statements are for debugging
                                if mdl_checker: 
                                    #print('we are inserting')
                                    split_cell.insert(neg_pos_mdl+1, "")
                                    #print('mdl_checker',split_cell)
                                    #print(split_cell)

                                #handling short dataset (analyte and result only)
                                #set 'result' in values_dict to the second of the two values
                                #print statements are for debugging
                                #print(current_headers)
                                #print(len(current_headers))
                                if len(current_headers) == 2:

                                    if(value_key.casefold() == 'result'.casefold()):
                                        cell_val = split_cell[-1]
                                        values_dict[value_key] = cell_val
                                        #print(cell_val)
                                    
                                    #assign analyte
                                    elif(value_key.casefold() == 'analyte'.casefold()):
                                        #print(value_key)
                                        analyte_name = ''
                                        for element in split_cell[:len(split_cell)-1]:
                                            analyte_name += element
                                            analyte_name += " "

                                        cell_val = analyte_name
                                        values_dict[value_key] = cell_val

                                        #print statements for debugging
                                        #print(values_dict)
                                        #print(cell_val)

                                #handle this first column of combined headers where there are more than 2 elements
                                elif len(current_headers) > 2:
                                    #handling qualifier
                                    if current_assign_dict['qualifier'] != None:
                                        #grab the second part of the tuple for 'qualifier' in the current_assign_dict (substring location within column)
                                        qualifier_location = current_assign_dict['qualifier'][1]

                                        #print statements for debugging
                                        #print('Qualifier location',qualifier_location)
                                        #print('for qualifier',current_headers)
                                        #print('for qualifier',split_cell)

                                        #calculate the actual length of the current cell
                                        split_header_length = len(split_cell)
                                        #calculate how the expected length based on the headers differs from the current length
                                        convert_factor = split_header_length - len(current_headers)

                                        #set qualifier defaults
                                        qual_count = 0 #set the initial count of qualifiers to zero
                                        qualifier_val = ''

                                        #find out qual_count
                                        for element in split_cell:
                                            if element in QUALIFIERS:
                                                if qual_count >0:
                                                    qualifier_val += " "
                                                qual_count += 1
                                                qualifier_val += element

                                        #find out how many qualifiers are expected
                                        expected_qualifiers = convert_factor+1
                                        #compare expected qualifiers with actual count of qualifiers found
                                        extra_elements = expected_qualifiers - qual_count


                                        if sub_index == qualifier_location:
                                            #we are dealing with the qualifier here

                                            #how man elements are in qualifier
                                            if qual_count == 0:
                                                cell_val = None #TODO: should this be set to ''?
                                            else:
                                                cell_val = qualifier_val.strip()

                                            #print("value for this cell is: ",cell_val)
                                            values_dict[value_key] = cell_val
                                            #print("expected num qualifiers",convert_factor+1)


                                        elif (sub_index > qualifier_location):
                                            #convert_factor = split_header_length - header_length

                                            #print call for debugging
                                            #print(split_cell)

                                            try:
                                                cell_val = split_cell[sub_index+convert_factor]
                                            except IndexError as e:
                                                cell_val = 'IndexError'

                                            #print calls for debugging
                                            #print(cell_val)
                                            #print("Key for this qualifier cell is:",value_key,"Value for this cell is", cell_val)

                                            #assign to values_dict
                                            values_dict[value_key] = cell_val

                                        #modify sub_index to account for spaces
                                        else:
                                            #sub_index is less than the qualifier location
                                            #were there an expected number of qualifiers?
                                            if sub_index == qualifier_location-1:
                                                try:
                                                    cell_val = split_cell[sub_index + extra_elements]
                                                    #print('Value for this cell is', cell_val)
                                                    values_dict[value_key] = cell_val
                                                except IndexError as ie:
                                                    print(ie)

                                            else:
                                                #For analyte, add elements from 0 to (0 + extra elements)
                                                analyte_name = ''
                                                for split in split_cell[0:1+extra_elements]:
                                                    analyte_name += (split + " ")

                                                cell_val = analyte_name.strip()
                                                #print('Value for this cell is', cell_val)
                                                values_dict[value_key] = cell_val

                                        #print calls for debugging
                                        #print("split cell length =", split_header_length)
                                        #print('header length is',header_length)

                            #handling sub_index recorded but not explicitly addressed
                            else:
                                #grab the value at the appropriate sub index
                                #print("X Value for this cell is",split_cell[sub_index])
                                try:
                                    cell_val = split_cell[sub_index]
                                    values_dict[value_key] = cell_val
                                except IndexError as ie:
                                    print(ie)

                        #handling keys with missing values
                        else:
                            #print("Y value_key is:", value_key)
                            cell_val = None
                            #print("Z Value for this cell is", cell_val)
                            values_dict[value_key] = cell_val

                    else:
                        #print("no processing needed for this line")
                        pass
                        
                    #add information to dictionary from dataframe, preparing to write to csv
                    values_dict['client_sample_id'] = d.loc[index]['client_sample_id']
                    values_dict['sample_date'] = d.loc[index]['sample_date']
                    values_dict['method'] = d.loc[index]['method']
                    values_dict['matrix'] = d.loc[index]['matrix']
                    #print("###")

                #print call for debugging
                #print(values_dict)

                if (values_dict['analyte'] != None and values_dict['analyte'] != ''):
                    #print calls for debugging
                    #print(current_headers)
                    #print(row2)
                    #print(values_dict)

                    if ((values_dict['method'] != 'General Chemistry') and (values_dict['method'] != 'Part Size Red - Particle Size Reduction Preparation')):
                        print(values_dict)
                        #write to CSV
                        with open('norfolk_southern_data.csv','a',newline='') as f:
                            w = csv.writer(f)
                            w.writerow(values_dict.values())
                        pass

                    #visually separate printed values_dict as we iterate
                    print("###")

            #set last_sample variable to the current sample id
            last_sample = client_sample_id

    #print calls for debugging
    #test_string = '02/23/23'
    #test_string_2 = '12:00'
    #print(is_date_1(test_string))
    #print(is_date_2(test_string))
    #print(is_date_2(test_string_2))
    #print(is_date_1(test_string_2))
            
    #test_list = ['Mercury', 'ND', '0.0020', '0.00013', 'mg/L', '02/23/23', '12:00', '']
    #strip_datetime(test_list)
            
#call function
test_pages = '1-16'
scrape_eurofins_pdf(path_1,pages_1)
scrape_eurofins_pdf(path_2,pages_2)