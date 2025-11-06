from flask import Flask, request, jsonify
from flask_cors import CORS
from icmplib import ping

app = Flask(__name__)
CORS(app) 

@app.route('/ping')
def icmp_ping_check():
    host = request.args.get("host", "8.8.8.8")
    
    try:
        count = int(request.args.get("count", 3))
    except ValueError:
        return jsonify({"error": "قيمة 'count' يجب أن تكون عدد صحيح (Integer)."}), 400
    
    try:
        timeout = float(request.args.get("timeout", 2.0))
    except ValueError:
        return jsonify({"error": "قيمة 'timeout' يجب أن تكون رقماً (Float)."}), 400

    try:
        result = ping(host, count=count, timeout=timeout)
        
        response_data = {
            "query_host": result.address,
            "packets_sent": result.packets_sent,
            "packets_received": result.packets_received,
            "packet_loss_percent": result.packet_loss * 100,
            "is_alive": result.is_alive,
            "minimum_rtt_ms": result.min_rtt,
            "average_rtt_ms": result.avg_rtt,
            "maximum_rtt_ms": result.max_rtt,
            "latency_details": [r.time * 1000 for r in result.packets if r is not None]
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": f"فشل في تنفيذ Ping: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
