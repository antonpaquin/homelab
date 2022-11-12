FROM pytorch/pytorch:1.13.0-cuda11.6-cudnn8-runtime

RUN apt update && apt install -y git curl
RUN apt-get install -y ffmpeg libsm6 libxext6

RUN curl https://raw.githubusercontent.com/AUTOMATIC1111/stable-diffusion-webui/master/requirements_versions.txt > requirements.txt && pip install -r requirements.txt
RUN conda install -y --force-reinstall markupsafe==2.0.1
RUN git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui

RUN cd stable-diffusion-webui && python -c 'from launch import prepare_enviroment; prepare_enviroment()' --skip-torch-cuda-test

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]