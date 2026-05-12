from football_ml.web.app import app
import os
import traceback
from flask import jsonify

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the full traceback
    print(traceback.format_exc())
    return jsonify({
        "error": str(e),
        "traceback": traceback.format_exc()
    }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)
