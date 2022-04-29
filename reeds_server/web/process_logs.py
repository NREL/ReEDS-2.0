

import os
import datetime
from web.create_db import RequestMetric, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import boto3

def process_logs(folder_path, session, bucket_name):

    request_data = {}
    files_to_be_deleted = []
    for file in os.listdir(folder_path):

        if len(file.split('.')) == 3:

            with open(os.path.join(folder_path, file), "r") as f:
                log_lines = f.readlines()

            for line in log_lines:
                if 'http' in line and 'Time spent processing request' in line:
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
            files_to_be_deleted.append(file)

        
    if request_data:
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

    for file in files_to_be_deleted:
        # Let's push to s3
        s3_client = boto3.client('s3')
        try:
            response = s3_client.upload_file(os.path.join(folder_path, file), bucket_name, file )
            os.remove(os.path.join(folder_path, file))
        except Exception as e:
            print(e)
        

if __name__ == '__main__':
    process_logs(r'C:\Users\KDUWADI\Desktop\NREL_Projects\ReEDs\logs')
