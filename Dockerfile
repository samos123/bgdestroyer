FROM python:3.9
RUN useradd bgremover -u 1000
RUN mkdir -p /home/bgremover && chown -R bgremover:bgremover /home/bgremover
USER bgremover
ENV PATH="/home/bgremover/.local/bin:${PATH}"
ENV PORT 8080
WORKDIR /home/bgremover
#ADD --chown=bgremover:bgremover https://drive.google.com/uc?id=1tCU5MM1LhRgGou5OpmpjBQbSrYIUoYab&confirm=t&uuid=061b1e0f-e73e-45b7-804a-e5bca062860f /home/bgremover/.u2net/u2net.onnx
COPY requirements.txt ./
RUN --mount=type=cache,target=/home/bgremover/.cache,uid=1000,gid=1000 pip3 install --user -r requirements.txt &&\
 curl -s https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Gull_portrait_ca_usa.jpg/1280px-Gull_portrait_ca_usa.jpg |\
 rembg i > /dev/null
COPY --chown=1000:1000 src/. .
CMD exec gunicorn --bind :$PORT --workers 1 --threads 1 --timeout 0 server:app
EXPOSE 8080
