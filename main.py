from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import tempfile
import subprocess
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, async_mode='threading')

LP_BIN = '/usr/bin/lpstat'
LPSTAT_BIN = '/usr/bin/lpstat'


@socketio.on('update')
def update_lpstas(data):
    def get_stats():
        while True:
            process = subprocess.Popen(
                [LP_BIN, '-W', 'completed'], stdout=subprocess.PIPE)
            completed = process.communicate()[0].decode('utf-8')
            process = subprocess.Popen(
                [LPSTAT_BIN, '-o'], stdout=subprocess.PIPE)
            queued = process.communicate()[0].decode('utf-8')
            yield completed, queued

    for completed, queued in get_stats():
        emit('update', {'completed': completed, 'queued': queued})
        time.sleep(2)


@app.route('/stats')
def stats():
    process = subprocess.Popen(
        [LP_BIN, '-W', 'completed'], stdout=subprocess.PIPE)
    completed = process.communicate()[0].decode('utf-8')
    process = subprocess.Popen(
        [LPSTAT_BIN, '-o'], stdout=subprocess.PIPE)
    queued = process.communicate()[0].decode('utf-8')
    return render_template('stats.html', completed=completed, queued=queued)


@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']

        with tempfile.NamedTemporaryFile() as temp:
            f.save(temp.name)
            subprocess.run([LP_BIN, "-d", "Brother_MFC-7360N", temp.name])
            return redirect(url_for('stats'))


if __name__ == '__main__':
    socketio.run(app, debug=True)
