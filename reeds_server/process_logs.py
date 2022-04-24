

import os
import datetime
from web.create_db import RequestMetric, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

conn_string = r'mysql://root:kapil@localhost:3306/reeds'

def process_logs(folder_path):

    engine = create_engine(conn_string)
    Base.metadata.bind = engine 
    db_session = sessionmaker(bind=engine)

    session = db_session()

    request_data = {}
    for file in os.listdir(folder_path):
        
        # log_date = datetime.datetime.strptime(file.split('.')[2], "%Y-%m-%d")
        # print(log_date)

        with open(os.path.join(folder_path, file), "r") as f:
            log_lines = f.readlines()

        for line in log_lines:
            if 'http' in line:
                line_content = line.split(' ')[-4:]
                url_name = line_content[0].split('api/')[1]
                request_time = round(float(line_content[2])*1000,3)
                log_time = datetime.datetime.strptime(line.split(',')[0],'%Y-%m-%d %H:%M:%S')
                
                key_name = datetime.datetime(log_time.year, log_time.month, log_time.day, log_time.hour).strftime('%Y-%m-%d %H:%M:%S')
                if key_name not in request_data:
                    request_data[key_name] = {}
                
                if url_name not in request_data[key_name]:
                    request_data[key_name][url_name] = []

                request_data[key_name][url_name].append(request_time)
    
    request_data_mod = {}
    for time_key, subdict in request_data.items():
        request_data_mod[time_key] = {}
        for api, request_times in subdict.items():
            if  len(api)< 100:
                request_data_mod[time_key][api] = max(request_times)

                rm = RequestMetric()
                rm.req_name = api
                rm.req_date = datetime.datetime.strptime(time_key, '%Y-%m-%d %H:%M:%S')
                rm.req_time = int(max(request_times))
                session.add(rm)
    
    session.commit()
    session.close()
    print(request_data_mod)




if __name__ == '__main__':
    process_logs(r'C:\Users\KDUWADI\Desktop\NREL_Projects\ReEDs\logs')
