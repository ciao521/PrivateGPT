FROM codercom/code-server

USER root

# update
RUN apt update
RUN apt upgrade -y
RUN apt install python3-pip tzdata htop -y
RUN apt autoremove -y
RUN apt clean

# timezone
RUN ln -fs /usr/share/zoneinfo/Asia/Bangkok /etc/localtime
RUN dpkg-reconfigure --frontend noninteractive tzdata

# pip
COPY entrypoint.sh /usr/bin
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
