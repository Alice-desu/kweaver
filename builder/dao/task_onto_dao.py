# -*-coding:utf-8-*-
from utils.my_pymysql_pool import connect_execute_commit_close_db, connect_execute_close_db
import arrow
import pandas as pd
import datetime
import configparser
import redis
import json
from utils.log_info import Logger
from flask import request
class TaskDaoOnto(object):
    # 初始化redis
    def getredisConnect(self):
        from utils.ConnectUtil import redisConnect
        return redisConnect

    def initredis_onto(self):
        try:
            redisConnect = self.getredisConnect()
            r = redisConnect.connect_redis(db=11,model="read")
            w = redisConnect.connect_redis(db=11,model="write")
            # keys = r.keys()
            df = task_dao_onto.get_otl_Count()
            # print(df)
            # 获得任务列表中的所有task_id
            df_taskid = df["celery_task_id"]
            df_taskid_list = df_taskid.values.tolist()
            for taskid in df_taskid_list:
                key = "celery-task-meta-" + taskid
                data = r.get(key)
                data = data.decode("utf-8")
                redisdata = json.loads(data)
                status = redisdata["status"]
                task_id = redisdata["task_id"]
                k_v = "celery-task-meta-" + task_id
                from datetime import datetime
                utc_time = datetime.utcnow().isoformat()
                va = {
                    "status": "REVOKED",
                    "result": {
                        "current": "builder server restart and stop task"
                    },
                    "traceback": "null",
                    "children": [],
                    "date_done": utc_time,
                    "task_id": task_id
                }
                status_diy = ["PENDING", "RUNNING"]
                if status in status_diy:
                    w.set(k_v, json.dumps(va).encode())
        except Exception as e:
            err = repr(e)
            if "service not known" in err:
                print("service not known!")
            elif "No route to host" in err:
                print("No route to host!")
            elif "DB index is out of range" in err:
                print("DB index is out of range!")
            else:
                print("redis is down!-5")


    # 遍历redis 获得任务的信息，供定时刷新用
    def get_otl_taskall(self,df_taskid_list):
        try:
            redisConnect = self.getredisConnect()
            r = redisConnect.connect_redis(db=11,model="read")
            # keys = r.keys()

            task_id = []
            status = []
            date_done_list = []
            result = []
            all_res = []
            # for i in keys:
            #     key = i.decode("utf-8")
            #     taskid_key = key.split("celery-task-meta-")
            if len(df_taskid_list)!= 0:
                for  taskid in df_taskid_list:
                    # print(taskid_key[1])
                    key =  "celery-task-meta-"+str(taskid)
                    data = r.get(key)
                    if data != None:
                        data = data.decode("utf-8")
                        redisdata = json.loads(data)
                        task_id.append(redisdata["task_id"])
                        status.append(redisdata["status"])
                        date_done = redisdata["date_done"]
                        if date_done is None:
                            end_time = "None"
                        else:
                            date_done = date_done.split(".")[0]
                            UTC_FORMAT = "%Y-%m-%dT%H:%M:%S"
                            utcTime = datetime.datetime.strptime(date_done, UTC_FORMAT)
                            end_time = utcTime + datetime.timedelta(hours=8)
                        date_done_list.append(str(end_time))
                        redisdata["date_done"] = str(end_time)
                        result.append(redisdata["result"])
                        all_res.append(redisdata)



            df = pd.DataFrame({"task_id": task_id, "status": status, "date_done": date_done_list,
                               "result": result, "all_res": all_res})
            return 200, df
        except Exception as e:
            err = repr(e)
            print(err)
            if "No route to host" in err:
                return "400", "No route to host!"
            elif "service not known" in err:
                return "400", "service not known!"
            elif "DB index is out of range" in err:
                return "400", "DB index is out of range!"
            else:
                return "400", str(err)+"8"


    @connect_execute_commit_close_db
    def delete_otl_task(self, task_id, connection, cursor):
        sql = """DELETE FROM ontology_task_table WHERE task_id= %s""" % (str(task_id))

        cursor.execute(sql)
        new_id = cursor.lastrowid
        return new_id
        # 删除任务列表


    @connect_execute_commit_close_db
    def insert_otl_Data(self, otl_id,task_name,ds_id,task_type,postfix, connection, cursor):
        values_list = []
        # values_list.append(str(email))
        values_list.append(str(task_name))
        values_list.append(str(ds_id))
        # values_list.append('"'+str(table_list)+'"')
        values_list.append(str(task_type))
        values_list.append(str(postfix))
        values_list.append(str(arrow.now().format('YYYY-MM-DD HH:mm:ss')))
        values_list.append(str(otl_id))
        sql = """INSERT INTO ontology_task_table (task_name, ds_id, task_type,postfix,create_time,ontology_id) VALUES(%s,%s,%s,%s,%s,%s)"""
        cursor.execute(sql, values_list)
        new_id = cursor.lastrowid
        return new_id


    @connect_execute_close_db
    def get_otl_Count(self, connection, cursor,):
        sql = """
                SELECT * FROM ontology_task_table;
                """
        df = pd.read_sql(sql, connection)
        return df


    @connect_execute_commit_close_db
    def update_otl_statusbyid(self, status, error_report, celery_task_id,task_id,finished_time, connection, cursor):
        values_list = []
        values_list.append(str(status))
        error_report = str(error_report)
        # error_report = error_report.replace('"', "'")
        values_list.append(error_report)
        values_list.append(str(celery_task_id))
        if finished_time != "None":
            values_list.append(str(finished_time))
        else :
            values_list.append(str("-"))
        values_list.append(str(task_id))
        if error_report == "":
            sql = """UPDATE ontology_task_table SET task_status=%s ,  celery_task_id = %s ,finished_time = %s  WHERE task_id=%s"""
            sql = sql % ('"' + values_list[0] + '"', '"'+values_list[2]+'"','"'+ values_list[3]+'"', values_list[4])
        else:
            sql = """UPDATE ontology_task_table SET task_status=%s,result=%s, celery_task_id = %s,finished_time = %s  WHERE task_id=%s"""
            sql = sql % ('"' + values_list[0] + '"', '"' +str(values_list[1])+ '"',  '"'+values_list[2]+'"','"' +values_list[3]+ '"',values_list[4])



        cursor.execute(sql)
        new_id = cursor.lastrowid
        return new_id

    @connect_execute_commit_close_db
    def update_otl_status_byceleryid(self, status, error_report, celery_task_id,finished_time, connection, cursor):
        values_list = []
        values_list.append(str(status))
        error_report = str(error_report)
        error_report=error_report.replace('"',"'")
        # error_report = error_report.replace("'",'"')
        values_list.append(error_report)
        if finished_time != "None":
            values_list.append(str(finished_time))
        else :
            values_list.append("-")
        values_list.append(str(celery_task_id))

        # values_list.append(str(task_id))
        if error_report == "":
            sql = """UPDATE ontology_task_table SET task_status=%s , finished_time = %s WHERE celery_task_id = %s"""
            sql = sql % ('"' + values_list[0] + '"', '"'+values_list[2]+'"','"'+ values_list[3]+'"')
        else:
            sql = """UPDATE ontology_task_table SET task_status=%s , result=%s ,finished_time = %s  WHERE celery_task_id = %s """
            sql = sql % ( '"' + values_list[0] + '"','"' + str(values_list[1])+ '"','"' + values_list[2]+ '"' ,'"' + values_list[3] + '"')
        cursor.execute(sql)
        new_id = cursor.lastrowid
        return new_id

    @connect_execute_close_db
    def get_task_by_task_id( self,task_id,connection, cursor):
        sql = """
            SELECT *
            FROM ontology_task_table
            where task_id = %s""" % (str(task_id))
        df = pd.read_sql(sql, connection)
        # data=df.to_dict()
        return df

    @connect_execute_close_db
    def get_all_otl_task(self,page,size,status,otl_id,connection, cursor):
        if status!="all":
            sql = """SELECT task_name,task_id,celery_task_id,task_status,task_type FROM ontology_task_table where task_status = %s  AND  ontology_id=%s order by create_time  Desc limit %s, %s""" % ('"'+str(status)+'"','"'+str(otl_id)+'"',str(int(page) * int(size)),str(size))
            # sql = sql.format()
        else:
            sql = """SELECT task_name,task_id,celery_task_id,task_status,task_type  FROM ontology_task_table WHERE ontology_id=%s AND task_status IN ("finished","failed","running")  ORDER BY task_status DESC, create_time DESC limit %s, %s""" % (
            '"' + str(otl_id) + '"', str(int(page) * int(size)), str(size))
        df = pd.read_sql(sql, connection)
        # data=df.to_dict()
        return df

    @connect_execute_close_db
    def get_all_by_otlid(self, otl_id, connection, cursor):

        sql = """SELECT * FROM ontology_task_table where ontology_id=%s and task_status not in ("failed")"""% ('"'+str(otl_id)+'"')
        # sql = sql.format()
        df = pd.read_sql(sql, connection)
        # data=df.to_dict()
        return df

    @connect_execute_close_db
    def getrunningtask(self,connection, cursor):
        sql = """select * from ontology_task_table"""
        df = pd.read_sql(sql, connection)
        # data=df.to_dict()
        return df


    @connect_execute_close_db
    def get_all_otl_task_result(self,used_task,otl_id,connection, cursor):
        used_info=",".join([str(i) for i in used_task])
        status="finished"
        if used_info!="":

            sql = """SELECT task_id , result ,ds_id ,postfix FROM ontology_task_table where task_id NOT IN (%s) AND task_status=%s AND ontology_id=%s"""%(used_info,'"'+status+'"','"'+str(otl_id)+'"')
        # sql = sql.format()
        else:

            sql="""SELECT task_id , result ,ds_id ,postfix FROM ontology_task_table where task_status=%s AND ontology_id=%s """%('"'+status+'"','"'+str(otl_id)+'"')
        df = pd.read_sql(sql, connection)
        # data=df.to_dict()
        return df

    @connect_execute_close_db
    def get_finished_otl_task_result(self,otl_id,connection, cursor):
        status = "running"

        sql = """SELECT task_id FROM ontology_task_table where task_status=%s AND ontology_id=%s""" % ('"'+status+'"','"'+str(otl_id)+'"')
        # sql = sql.format()
        df = pd.read_sql(sql, connection)
        # data=df.to_dict()
        return df

    @connect_execute_commit_close_db
    def add_file_status(self,file_list,task_id,connection, cursor):
        sql="""UPDATE ontology_task_table SET file_list=%s WHERE celery_task_id=%s	"""%('"'+str(file_list)+'"','"'+str(task_id)+'"')
        # sql = sql.format()
        cursor.execute(sql)
        new_id = cursor.lastrowid
        return new_id

    @connect_execute_close_db
    def get_multi_filesname(self, otl_id,connection, cursor):

        sql="""select *  from ontology_task_table where ontology_id=%s and task_type=%s"""%('"'+str(otl_id)+'"','"'+"multi-files"+'"')
        df = pd.read_sql(sql, connection)
        return df

    @connect_execute_close_db
    def get_all_task_from_otl_table(self,otl_id,connection, cursor):
        sql="""select all_task from ontology_table where id =%s"""%('"'+str(otl_id)+'"')
        df = pd.read_sql(sql, connection)
        return df

    @connect_execute_commit_close_db
    def update_task_by_otl_temp(self,otl_temp,otl_id,connection, cursor):
        ###otl_temp=""
        sql = """UPDATE ontology_task_table SET ontology_id=%s,otl_temp="" WHERE  otl_temp=%s""" % ('"'+str(otl_id)+'"','"'+str(otl_temp)+'"')
        cursor.execute(sql)
        new_id = cursor.lastrowid
        return new_id

    @connect_execute_close_db
    def get_max_id(self,  connection, cursor):
        sql="SELECT * FROM ontology_task_table ORDER BY task_id DESC LIMIT 1"
        df = pd.read_sql(sql, connection)
        return df

    @connect_execute_close_db
    def get_task_list(self,task_list, connection, cursor):
        sql = "SELECT * FROM ontology_task_table WHERE task_id IN (%s) "%(",".join([str(i) for i in task_list]))
        df = pd.read_sql(sql, connection)
        return df

    @connect_execute_close_db
    def get_otl_task_list(self, otlid_list, connection, cursor):
        sql = "SELECT * FROM ontology_task_table WHERE ontology_id IN (%s) " % (",".join([str(i) for i in otlid_list]))
        df = pd.read_sql(sql, connection)
        return df

    @connect_execute_commit_close_db
    def replace_task(self,temp_id,otl_id,connection, cursor):

        sql="INSERT INTO ontology_task_table (task_name,task_type,task_status,celery_task_id,result,file_list,otl_temp,create_time,ds_id,postfix) SELECT task_name,task_type,task_status,celery_task_id,result,file_list,ds_id,postfix, %s AS otl_temp,%s AS create_time FROM `ontology_task_table` WHERE ontology_id=%s"%('"'+str(temp_id)+'"','"'+arrow.now().format('YYYY-MM-DD HH:mm:ss')+'"','"'+str(otl_id)+'"')
        cursor.execute(sql)
        new_id = cursor.lastrowid
        return new_id

    @connect_execute_commit_close_db
    def update_otl_task_filelist(self,table_list, task_id,connection, cursor):
        sql="""UPDATE ontology_task_table SET file_list=%s WHERE  task_id=%s"""%('"'+str(table_list)+'"',task_id)
        cursor.execute(sql)
        new_id = cursor.lastrowid
        return new_id







task_dao_onto = TaskDaoOnto()