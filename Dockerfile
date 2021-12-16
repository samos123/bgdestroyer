FROM python:3.9
RUN useradd bgremover
RUN mkdir -p /home/bgremover && chown -R bgremover:bgremover /home/bgremover
USER bgremover
WORKDIR /home/bgremover

COPY requirements.txt ./
ENV PATH="/home/bgremover/.local/bin:${PATH}"
RUN pip3 install --user --no-cache-dir -r requirements.txt
COPY --chown=bgremover:bgremover src/. .
RUN python3 load-model.py
CMD [ "python3", "server.py" ]
