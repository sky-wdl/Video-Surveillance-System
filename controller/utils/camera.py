import cv2
import threading
import face_recognition


class RecordingThread(threading.Thread):
    def __init__(self, name, camera):
        threading.Thread.__init__(self)
        self.name = name
        self.isRunning = True

        self.cap = camera
        fourcc = cv2.VideoWriter_fourcc(*'MJPEG')
        self.out = cv2.VideoWriter('./A/video-One.avi', fourcc, 20.0, (640, 480))

    def run(self):
        while self.isRunning:
            ret, frame = self.cap.read()
            if ret:
                self.out.write(frame)

        self.out.release()

    def stop(self):
        self.isRunning = False

    def __del__(self):
        self.out.release()


class VideoCamera(object):
    def __init__(self):
        # 打开摄像头， 0代表笔记本内置摄像头
        self.face_encoding = None
        self.cap = cv2.VideoCapture(0)
        # 初始化人脸
        obama_img = face_recognition.load_image_file("obama.jpg")
        self.obama_face_encoding = face_recognition.face_encodings(obama_img)[0]

        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.process_this_frame = True

        # 初始化视频录制环境
        self.is_record = False
        self.out = None

        # 视频录制线程
        self.recordingThread = None

    # 退出程序释放摄像头
    def __del__(self):
        self.cap.release()

    def get_frame(self):
        ret, frame = self.cap.read()

        if ret:
            # 将视频帧调整为1/4大小，以加快脸部识别处理
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # 将图像从BGR颜色（OpenCV使用的）转换为RGB颜色（face_recognition使用）
            if self.process_this_frame:
                # 查找当前视频帧中的所有面部和脸部编码
                self.face_locations = face_recognition.face_locations(small_frame)
                self.face_encodings = face_recognition.face_encodings(small_frame, self.face_locations)
                self.face_names = []
                # 处理多张人脸的情况
                for self.face_encoding in self.face_encodings:
                    # 查看脸部是否与已知脸部相匹配（S）
                    match = face_recognition.compare_faces([self.obama_face_encoding], self.face_encoding)
                    if match[0]:
                        name = "WenDongliu"
                    else:
                        name = "unknown"
                    self.face_names.append(name)
            self.process_this_frame = not self.process_this_frame
            # 对有人脸的图进行处理
            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                # 自从我们检测到的框架缩放到1/4尺寸后，缩放后面的位置
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                # 在脸上画一个方框
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                # 在脸部下面画一个名字
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # 因为opencv读取的图片并非jpeg格式，因此要用motion JPEG模式需要先将图片转码成jpg格式图片
            ret, jpeg = cv2.imencode('.jpg', frame)

            # 视频录制
            if self.is_record:
                if self.out is None:
                    fourcc = cv2.VideoWriter_fourcc(*'MJPEG')
                    self.out = cv2.VideoWriter('./A/video-One.avi', fourcc, 20.0, (640, 480))

                ret, frame = self.cap.read()
                if ret:
                    self.out.write(frame)
            else:
                if self.out is not None:
                    self.out.release()
                    self.out = None

            return jpeg.tobytes()

        else:
            return None

    def start_record(self):
        self.is_record = True
        self.recordingThread = RecordingThread("视频录制线程", self.cap)
        self.recordingThread.start()

    def stop_record(self):
        self.is_record = False

        if self.recordingThread is not None:
            self.recordingThread.stop()
