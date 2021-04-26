# based on
#https://stackoverflow.com/questions/2887878/importing-a-csv-file-into-a-sqlite3-database-table-using-python
#https://sookocheff.com/post/tools/downloading-directories-of-code-from-github-using-the-github-api/
#https://jpmens.net/2019/04/04/i-clone-all-repositories-i-ve-starred/
#https://github.com/metmuseum/openaccess/raw/master/MetObjects.csv
import csv, sqlite3, pandas, sys, os, json, io
#pip install pandas
#from github import Github #get this working?
import requests#currently using 
DB_PATH = "curator.db"

#here lied a boatload of unused test code RIP

#class designed to see if github is updated and then download the csv file if it is
#warning as of right now downloads csv file every time
#quick fix recode
#https://stackoverflow.com/questions/38925115/sqlite3-operationalerror-near-syntax-error


class met_csv:
    #right now downloads the csv passed in from url and converts it to a dataframe
    def __init__(self):
        #location of csv
        self.url = 'https://github.com/metmuseum/openaccess/raw/master/MetObjects.csv'
        #switch comments to remove fast test mode on local csv
        self.df = pandas.read_csv(io.StringIO((requests.get(self.url).content).decode('utf-8')))
        
        #use this when testing for faster speed
        #self.df = pandas.read_csv('MetObjects.csv')
        print(self.df)
        self.unique_cols = {}
        self.is_good = False
    def parse_unique_classification(self,filters):
        #will return unique list of strings for values in 
        #that col not containing list of str filters

        #fix this. this is inefficient
        my_col = self.df.Classification.unique().tolist()
        for i in my_filters:
            my_col = [str(item) for item in my_col if str(i) not in str(item)]

        self.unique_cols.update({"Classification": my_col})
        self.is_good = True

        return my_col
    def update_classification_table(self):
        #horribly inefficient fix this
        #check needed to ensure 
        if self.is_good is True:
            try:
                conn=sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''DROP TABLE IF EXISTS classifications''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS classifications (Classification, Id, PRIMARY KEY (Classification))''')
                counter = 0
                for i in  self.unique_cols['Classification']:

                    cursor.execute('''INSERT INTO classifications VALUES (?,?)''', (i,counter))
                    counter= counter+1
                    #print(i, "inserted")

            except NameError:
                print("failed", NameError)
            print('table made?')
            conn.commit()
            

        return

def get_classifications(my_path):
    
    conn=sqlite3.connect(my_path)
    cursor = conn.cursor()
    query = ('''SELECT Classification FROM classifications;''')
    cursor.execute(query)
    rows =cursor.fetchall()
    
    temp = []

    for i in rows:
        temp.append(i[0])



    conn.commit()
    return temp


#example code on how to update download and update unique values to Classifications table in db
my_filters = ['|','/','-'] #characters to filter out of csv
cur_met_csv = met_csv() #create object containing csv loaded into pandas df
cur_met_csv.parse_unique_classification(my_filters) #convert df into list to filter and sort because
#I have little experience in pandas
cur_met_csv.update_classification_table() # add updated values to table in sql db
print(get_classifications(DB_PATH))#sanity check