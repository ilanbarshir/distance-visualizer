# Entry point for DigitalOcean App Platform
from distance_visualizer import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False) 