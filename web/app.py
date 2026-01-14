from flask import Flask, render_template
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import init_db


def create_app():
    import config
    
    app = Flask(
        __name__,
        template_folder=config.resolved_path('web/templates'),
        static_folder=config.resolved_path('web/static')
    )
    
    app.config['SECRET_KEY'] = 'lol-pro-stats-secret-key'
    app.config['JSON_SORT_KEYS'] = False
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    init_db()
    
    from web.routes.players import players_bp
    from web.routes.stats import stats_bp
    from web.routes.import_routes import import_bp
    
    app.register_blueprint(players_bp, url_prefix='/api')
    app.register_blueprint(stats_bp, url_prefix='/api')
    app.register_blueprint(import_bp, url_prefix='/api')
    
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
