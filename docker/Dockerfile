FROM python:3
WORKDIR /rtsp-server/
# RUN $(python3 -c 'import sys; print(sys.prefix)')
# RUN $(python3 -c 'from distutils.sysconfig import get_python_inc; print(get_python_inc())')
# RUN $(python3 -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')
# CMD ['python3', '-c', 'import sys; print(sys.prefix)']
# CMD ['python3', '-c', 'from distutils.sysconfig import get_python_inc; print(get_python_inc())']
# CMD ['python3', '-c', 'from distutils.sysconfig import get_python_lib; print(get_python_lib())']
RUN apt update
RUN pip install pycairo
RUN apt -y install libgirepository1.0-dev
RUN pip install PyGObject
RUN apt -y install libopencv-dev
# RUN apt -y install python3-opencv
# RUN pip install opencv-python
RUN apt -y install gir1.2-gst-rtsp-server-1.0
RUN apt -y install libgstreamer1.0-0
RUN apt -y install gstreamer1.0-plugins-base
RUN apt -y install gstreamer1.0-plugins-good
RUN apt -y install gstreamer1.0-plugins-bad
RUN apt -y install gstreamer1.0-plugins-ugly
RUN apt -y install gstreamer1.0-libav
RUN apt -y install gstreamer1.0-tools
RUN apt -y install gstreamer1.0-x
RUN apt -y install gstreamer1.0-alsa
RUN apt -y install gstreamer1.0-gtk3
RUN apt -y install gstreamer1.0-qt5
RUN apt -y install gstreamer1.0-pulseaudio
RUN apt -y install cmake
RUN git clone https://github.com/opencv/opencv.git
RUN git clone https://github.com/opencv/opencv_contrib.git
WORKDIR /rtsp-server/opencv
RUN mkdir build
WORKDIR /rtsp-server/opencv/build
RUN cmake -D CMAKE_BUILD_TYPE=RELEASE \
-D INSTALL_PYTHON_EXAMPLES=ON \
-D INSTALL_C_EXAMPLES=OFF \
-D PYTHON_EXECUTABLE=$(which python3) \
-D BUILD_opencv_python2=OFF \
-D CMAKE_INSTALL_PREFIX=/usr/local \
-D PYTHON3_EXECUTABLE=$(which python3) \
-D PYTHON3_INCLUDE_DIR=/usr/local/include/python3.10 \
-D PYTHON3_PACKAGES_PATH=/usr/local/lib/python3.10/site-packages \
-D WITH_GSTREAMER=ON \
-D BUILD_EXAMPLES=ON ..
RUN make -j$(nproc)
RUN make install
RUN ldconfig
WORKDIR /rtsp-server/