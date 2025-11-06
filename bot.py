from flask import Flask, request, jsonify
# نستخدم مكتبة icmplib لتحقيق فحص ICMP موثوق في بيئات الخادم
from icmplib import ping

app = Flask(__name__)

# المسار الرئيسي لتنفيذ فحص ICMP
@app.route('/ping')
def icmp_ping_check():
    # 1. استخلاص المُدخلات
    # المُضيف (Host): الافتراضي هو Google DNS (8.8.8.8)
    host = request.args.get("host", "8.8.8.8")
    
    # عدد الحزم (Count): الافتراضي 3، ويمكن زيادته (مثلاً إلى 50 لتحقيق 30 ثانية)
    try:
        count = int(request.args.get("count", 3))
    except ValueError:
        return jsonify({"error": "قيمة 'count' يجب أن تكون عدد صحيح (Integer)."}), 400
    
    # مهلة الانتظار للحزمة الواحدة (Timeout): الافتراضي 2 ثانية
    try:
        timeout = float(request.args.get("timeout", 2.0))
    except ValueError:
        return jsonify({"error": "قيمة 'timeout' يجب أن تكون رقماً (Float)."}), 400

    # 2. تنفيذ فحص Ping
    try:
        # icmplib.ping يرسل عدد الحزم المحدد
        result = ping(host, count=count, timeout=timeout)
        
        # 3. إعداد بيانات الإخراج (JSON)
        response_data = {
            "query_host": host,
            "packets_sent": result.packets_sent,
            "packets_received": result.packets_received,
            "packet_loss_percent": result.packet_loss * 100,
            "is_alive": result.is_alive,
            "minimum_rtt_ms": result.min_rtt,
            "average_rtt_ms": result.avg_rtt,
            "maximum_rtt_ms": result.max_rtt,
            "latency_details": [r.time * 1000 for r in result.packets if r is not None] # تحويل إلى قائمة تفاصيل زمن الاستجابة للحزم
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        # التعامل مع أي خطأ قد يحدث أثناء تنفيذ Ping (مثل عدم وجود المُضيف)
        return jsonify({"error": f"فشل في تنفيذ Ping: {e}"}), 500

# تشغيل التطبيق على المنفذ 5000 (الافتراضي لخوادم الويب البسيطة)
# Render و Replit سيكتشفان هذا تلقائياً
if __name__ == '__main__':
    # يجب ضبط هذا بناءً على بيئة الاستضافة
    app.run(host='0.0.0.0', port=5000)
