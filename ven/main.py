# -*- coding:utf-8 -*-
import cv2
from align_custom import AlignCustom
from face_feature import FaceFeature
from mtcnn_detect import MTCNNDetect
from tf_graph import FaceRecGraph
import argparse
import simplejson
import numpy as np
#2018-05-04 10:41:25.452080: I tensorflow/core/platform/cpu_feature_guard.cc:140] Your CPU supports instructions that this TensorFlow binary was not compiled to use: AVX2 FMA
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import pymysql
from Tkinter import *
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from PIL import ImageTk,Image





#使用电脑自带摄像头
def main(args):
    mode = args.mode;
    if (mode == "camera"):
        camera_recog();
    elif mode == "input":
        create_manual_data();
    else:
        raise ValueError("Unimplemented mode");

#调用电脑摄像头，视频识别
def camera_recog():
    print("[INFO] camera sensor warming up...")
    vs = cv2.VideoCapture(0);  # get input from webcam
    while True:
        _, frame = vs.read();
        rects, landmarks = face_detect.detect_face(frame, 80);
        aligns = []
        positions = []
        for (i, rect) in enumerate(rects):
            aligned_face, face_pos = aligner.align(160, frame, landmarks[i])
            if len(aligned_face) == 160 and len(aligned_face[0]) == 160:
                aligns.append(aligned_face)
                positions.append(face_pos)
            else:
                print("Align face failed")  # log
        if (len(aligns) > 0):
            features_arr = extract_feature.get_features(aligns)
            recog_data = findPeople(features_arr, positions);
            for (i, rect) in enumerate(rects):
                cv2.rectangle(frame, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]),
                              (255, 0, 0))  # draw bounding box for the face
                cv2.putText(frame, recog_data[i][0] + " - " + str(recog_data[i][1]) + "%", (rect[0], rect[1]),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
    # 释放摄像头并销毁所有窗口
    vs.release()
    cv2.destroyAllWindows()



#在数据集中寻找视频里面的人脸，有则显示user的ID，无则提示Unknown
def findPeople(features_arr, positions, thres=0.6, percent_thres=90):
    f = open('./facerec_128D.txt', 'r')
    data_set = simplejson.loads(f.read());
    returnRes = [];
    for (i, features_128D) in enumerate(features_arr):
        result = "Unknown";
        smallest = sys.maxsize
        for person in data_set.keys():
            person_data = data_set[person][positions[i]];
            for data in person_data:
                distance = np.sqrt(np.sum(np.square(data - features_128D)))
                if (distance < smallest):
                    smallest = distance;
                    result = person;
        percentage = min(100, 100 * thres / smallest)
        if percentage <= percent_thres:
            result = "Unknown"
        returnRes.append((result, percentage))
    return returnRes


#用于存储一张之前没有的人脸，输入ID，然后视频拍照获得数据q
def create_manual_data():
    vs = cv2.VideoCapture(0);  # get input from webcam

    ("Please input new user ID:")
    new_name = raw_input("please input new user ID:");  # ez python input()
    f = open('./facerec_128D.txt', 'r');
    data_set = simplejson.loads(f.read());
    person_imgs = {"Left": [], "Right": [], "Center": []};
    person_features = {"Left": [], "Right": [], "Center": []};
    print("Please start turning slowly. Press 'q' to save and add this new user to the dataset");
    while True:
        _, frame = vs.read();
        rects, landmarks = face_detect.detect_face(frame, 80);  # min face size is set to 80x80
        for (i, rect) in enumerate(rects):
            aligned_frame, pos = aligner.align(160, frame, landmarks[i]);
            if len(aligned_frame) == 160 and len(aligned_frame[0]) == 160:
                person_imgs[pos].append(aligned_frame)
                cv2.imshow("Captured face", aligned_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    for pos in person_imgs:  # there r some exceptions here, but I'll just leave it as this to keep it simple
        person_features[pos] = [np.mean(extract_feature.get_features(person_imgs[pos]), axis=0).tolist()]
    data_set[new_name] = person_features;

    # 释放摄像头并销毁所有窗口
    vs.release()
    cv2.destroyAllWindows()

    # 获取游标
    cursor = conn.cursor()
    # 2数据库中插入数据
    sql_insert = "INSERT INTO data(userID,feature) values('%s','%s')"%(new_name,simplejson.dumps(data_set[new_name]))
    # 执行语句
    cursor.execute(sql_insert)
    # 事务提交，否则数据库得不到更新
    conn.commit()
    print(cursor.rowcount)
    # 数据库连接和游标的关闭
    conn.close()
    cursor.close()
    f = open('./facerec_128D.txt', 'w');
    f.write(simplejson.dumps(data_set))
    f.close()


#删除人脸数据信息
def delete_existing_data():
    #文件中删除
    f = open('./facerec_128D.txt', 'rw');
    data_set=simplejson.loads(f.read());
    for key in data_set.keys():
        print key
    user = raw_input("Please input userID you want to delete:\n")
    del data_set[user]
    f=open('./facerec_128D.txt','w');
    f.write(simplejson.dumps(data_set));
    f.close()
    print "Delete done!"

    #数据库删除
    # 获取游标
    cursor = conn.cursor()
    # 3从数据库中删除数据
    sql_delete="DELETE FROM data WHERE userID=('%s')" % (user)
    # 执行语句
    cursor.execute(sql_delete)
    # 事务提交，否则数据库得不到更新
    conn.commit()
    print(cursor.rowcount)
    # 数据库连接和游标的关闭
    conn.close()
    cursor.close()

#读取人脸数据信息
def viewing_data():
    #文件中读取
    f=open('./facerec_128D.txt','r')
    data_set=simplejson.loads(f.read())
    for key in data_set.keys():
        print key
    ans=raw_input("Please input the ID to see the person:\n")
    f.close()

    # 获取游标
    cursor = conn.cursor()
    # 4从数据库中读取数据
    sql_select="SELECT userID FROM data"
    # 执行语句
    cursor.execute(sql_select)
    # 事务提交，否则数据库得不到更新
    conn.commit()
    print(cursor.rowcount)
    # 数据库连接和游标的关闭
    conn.close()
    cursor.close()
    return data_set[ans]

if __name__ == '__main__':

    '''
    用GUI界面做的时候在每个按钮里面重新写了上面的四个方法
    用后面的控制台程序执行的时候调用上面四个方法
    提示：增加人脸特征数据和删除人脸特征数据到数据库中的时候一定要确保数据库是连接状态
    '''

    #1、识别人脸
    #2、增加人脸数据
    #3、删除人脸数据
    #4、查看已有人脸数据

    #连接mysql数据库，这个连接数据库代码是用于通过控制台运行程序
    conn = pymysql.Connect(
        host='localhost',
        port=3306,
        user='root',
        passwd='123456',
        db='facerec',
        charset='utf8'
    )

    #加载模型
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, help="Run camera recognition", default="camera")
    args = parser.parse_args(sys.argv[1:]);
    FRGraph = FaceRecGraph();
    aligner = AlignCustom();
    extract_feature = FaceFeature(FRGraph)
    face_detect = MTCNNDetect(FRGraph, scale_factor=2);  # scale_factor, rescales image for faster detection

    #GUI程序
    Bu = Tk()
    #控制窗口大小
    Bu.geometry('200x400')
    Bu.title('主菜单')
    # 回调函数
    def PrintButton1():
        camera_recog()        # 调用摄像头识别人脸
    def PrintButton2():
        #连接数据库
        conn = pymysql.Connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='123456',
            db='facerec',
            charset='utf8'
        )

        Add=Tk('100x350')
        Add.title('增加')
        Label(Add,text='请输入人员姓名:').pack()
        e=Entry(Add)
        e.pack()
        def insert_Text():
            new_name=e.get()
            vs = cv2.VideoCapture(0);  # get input from webcam

            f = open('./facerec_128D.txt', 'r');
            data_set = simplejson.loads(f.read());
            person_imgs = {"Left": [], "Right": [], "Center": []};
            person_features = {"Left": [], "Right": [], "Center": []};
            print("Please start turning slowly. Press 'q' to save and add this new user to the dataset");
            while True:
                _, frame = vs.read();
                rects, landmarks = face_detect.detect_face(frame, 80);  # min face size is set to 80x80
                for (i, rect) in enumerate(rects):
                    aligned_frame, pos = aligner.align(160, frame, landmarks[i]);
                    if len(aligned_frame) == 160 and len(aligned_frame[0]) == 160:
                        person_imgs[pos].append(aligned_frame)
                        cv2.imshow("Captured face", aligned_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

            for pos in person_imgs:  # there r some exceptions here, but I'll just leave it as this to keep it simple
                person_features[pos] = [np.mean(extract_feature.get_features(person_imgs[pos]), axis=0).tolist()]
            data_set[new_name] = person_features;
            # 释放摄像头并销毁所有窗口
            vs.release()
            cv2.destroyAllWindows()

            # 向文件中写入数据
            f = open('./facerec_128D.txt', 'w');
            f.write(simplejson.dumps(data_set))

            # 获取游标
            cursor = conn.cursor()
            # 数据库中插入数据
            sql_insert = "INSERT INTO data(userID,feature) VALUES('%s','%s')" % (
                new_name.decode('utf-8'), simplejson.dumps(data_set[new_name]).decode('utf-8'))
            # 执行语句
            cursor.execute(sql_insert)
            # 事务提交，否则数据库得不到更新
            conn.commit()
            print(cursor.rowcount)
            # 数据库连接和游标的关闭
            conn.close()
            cursor.close()
            f.close()
            t.insert('end', 'Add ' + new_name + ' done.')

        Button(Add,text='确定',command=insert_Text).pack()
        t=Text(Add,width=50,height=2)
        t.pack()

    def PrintButton3():
        Delete=Tk('100x350')
        Delete.title('删除')
        Label(Delete,text='已有数据').pack()
        t1=Text(Delete,width=50,height=8)
        f = open('./facerec_128D.txt', 'r')
        data_set = simplejson.loads(f.read())
        for key in data_set.keys():
            t1.insert(1.0, key + '\n')
        f.close()
        t1.pack()
        Label(Delete,text='要删除数据：').pack()
        e=Entry(Delete)
        e.pack()
        t=Text(Delete,width=50,height=2)
        def delete_data():
            # 文件中删除f
            #先清空text
            t.delete(0.0,END)
            f = open('./facerec_128D.txt', 'rw');
            data_set = simplejson.loads(f.read());
            user = e.get()
            answer=False
            for key in data_set.keys():
                if key==user:
                    answer=True
            if answer:
                del data_set[user]
                f = open('./facerec_128D.txt', 'w');
                f.write(simplejson.dumps(data_set));

                # 数据库删除
                # 获取游标
                conn = pymysql.Connect(
                    host='localhost',
                    port=3306,
                    user='root',
                    passwd='123456',
                    db='facerec',
                    charset='utf8'
                )

                cursor = conn.cursor()
                # 从数据库中删除数据
                sql_delete = "DELETE FROM data WHERE userID=('%s')" % (user)
                # 执行语句
                cursor.execute(sql_delete)
                # 事务提交，否则数据库得不到更新
                conn.commit()
                # print(cursor.rowcount)
                # 数据库连接和游标的关闭
                conn.close()
                cursor.close()
                f.close()
                t.insert(1.0, 'Delete ' + user + ' done.' + '\n')
                t.pack()
            else:
                t.insert(1.0, 'Not find ' + user+'!'+'\n')
                t.pack()
        Button(Delete,text='确定',command=delete_data).pack()
    def PrintButton4():
        #连接数据库
        conn = pymysql.Connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='123456',
            db='facerec',
            charset='utf8'
        )

        View=Tk()
        View.title('查看')
        View.geometry('250x400')
        t=Text(View)
        Label(View,text='已有成员数据',justify = 'left').pack()
        t1=Text(View,width=50,height=10)
        f = open('./facerec_128D.txt', 'r')
        data_set = simplejson.loads(f.read())
        for key in data_set.keys():
            t1.insert(1.0, key+'\n')
        f.close()
        t1.pack()
        Label(View,text='请输入姓名：').pack()
        e=Entry(View)
        e.pack()
        #设置滑轮
        s=Scrollbar(View)
        s.pack(side=RIGHT, fill=Y)
        s.config(command=t.yview)
        t.config(yscrollcommand=s.set)
        def view_data():
            t.delete(0.0,END)
            f = open('./facerec_128D.txt', 'r')
            data_set = simplejson.loads(f.read())
            ans = e.get()
            answer=False
            for key in data_set.keys():
                if key==ans:
                    answer=True
                    break
            if answer==False:
                t.insert(1.0, 'Not find ' + ans+'!')
                t.pack()
            else:
                t.insert(1.0, data_set[ans])
                t.pack()
            f.close()

            # 获取游标
            cursor = conn.cursor()
            # 4从数据库中读取数据
            sql_select = "SELECT userID FROM data"
            # 执行语句
            cursor.execute(sql_select)
            # 事务提交，否则数据库得不到更新
            conn.commit()
            print(cursor.rowcount)
            # 数据库连接和游标的关闭
            conn.close()
            cursor.close()
        Button(View,text='确定',command=view_data).pack()




    Label(Bu,text='1、识别人脸\n2、增加人脸数据\n3、删除人脸数据\n4、查看已有人脸数据'  ,justify = 'left').pack()
    Button(Bu,text='press1',anchor='c',bg='blue',command=PrintButton1, width=15, ).pack()
    Button(Bu, text='press2', anchor='c', bg='blue', command=PrintButton2, width=15).pack()
    Button(Bu, text='press3', anchor='c', bg='blue', command=PrintButton3, width=15).pack()
    Button(Bu, text='press4', anchor='c', bg='blue', command=PrintButton4, width=15).pack()
    im=Image.open('picture.jpg')
    image=im.resize((200,300),Image.ANTIALIAS)
    photo=ImageTk.PhotoImage(image)

    Label(Bu,image=photo).pack()
    Bu.mainloop()


    #控制台程序
    '''choice = int(raw_input("Please input your choice:\n"))
    if choice == 1:
        parser = argparse.ArgumentParser()
        parser.add_argument("--mode", type=str, help="Run camera recognition", default="camera")
        args = parser.parse_args(sys.argv[1:]);
        FRGraph = FaceRecGraph();
        aligner = AlignCustom();
        extract_feature = FaceFeature(FRGraph)
        face_detect = MTCNNDetect(FRGraph, scale_factor=2);  # scale_factor, rescales image for faster detection
        # main(args);  #调用摄像头识别人脸
        camera_recog()
    if choice == 2:
        parser = argparse.ArgumentParser()
        parser.add_argument("--mode", type=str, help="Run camera recognition", default="camera")
        args = parser.parse_args(sys.argv[1:]);
        FRGraph = FaceRecGraph();
        aligner = AlignCustom();
        extract_feature = FaceFeature(FRGraph)
        face_detect = MTCNNDetect(FRGraph, scale_factor=2);  # scale_factor, rescales image for faster detection
        create_manual_data()  # 增加新的人脸数据
    if choice == 3:
        delete_existing_data()  # 删除人脸数据
    if choice ==4:   #查看人脸数据
        viewing_data()'''

