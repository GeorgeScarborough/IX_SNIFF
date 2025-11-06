from flask import Flask, request, jsonify
import ping3
import socket

# يجب عليك تثبيت مكتبة ping3: pip install ping3

app = Flask(__name__)

# إعداد المكتبة لتعمل في وضع غير مميز (بدون صلاحيات Root)
# هذه القيمة تجعل ping3 تستخدم مقابس UDP/TCP بدلاً من ICMP الخام إذا لم تتوفر صلاحيات Root
ping3.EXCEPTIONS = True 
ping3.DEFAULT_TIMEOUT = 3 

@app.route('/ping', methods=['GET'])
def ping_host():
    """
    تنفيذ فحص ICMP Ping على مضيف محدد باستخدام مكتبة ping3.
    الوصول: /ping?host=<IP_OR_HOSTNAME>
    """
    host = request.args.get('host')
    
    if not host:
        return jsonify({
            "status": "error",
            "error": "الرجاء تحديد معامل المضيف (host) في رابط URL."
        }), 400

    # محاولة حل اسم المضيف إلى IP لضمان إمكانية الوصول
    try:
        ip_address = socket.gethostbyname(host)
    except socket.gaierror:
        return jsonify({
            "status": "error",
            "error": f"تعذر حل اسم المضيف: {host}"
        }), 400

    try:
        # تنفيذ Ping بخمس حزم
        results = []
        packets_to_send = 5
        packets_lost = 0

        for _ in range(packets_to_send):
            # استخدام مكتبة ping3 لفحص Ping
            delay = ping3.ping(ip_address, unit='ms')
            
            if isinstance(delay, float):
                results.append(delay)
            elif delay is False:
                # Delay is False if the ping timed out or failed (equivalent to packet loss)
                packets_lost += 1

        
        if not results and packets_lost == packets_to_send:
            # إذا لم يتم استلام أي حزمة على الإطلاق
            avg_rtt = None
            packet_loss_percentage = 100.0
            status_text = "فشل كامل في الاتصال"
        else:
            # حساب المتوسط إذا كان هناك نتائج ناجحة
            avg_rtt = sum(results) / len(results) if results else 0.0
            packet_loss_percentage = (packets_lost / packets_to_send) * 100.0
            status_text = "نجاح"
        
        return jsonify({
            "status": status_text,
            "host": host,
            "ip_address": ip_address,
            "packets_sent": packets_to_send,
            "packets_received": len(results),
            "packet_loss": round(packet_loss_percentage, 2),
            "avg_rtt": round(avg_rtt, 2) if avg_rtt is not None else None
        })

    except ping3.errors.HostUnknown:
        return jsonify({
            "status": "error",
            "error": "تعذر حل اسم المضيف أو عنوان IP غير صالح."
        }), 400
    except ping3.errors.PingError as e:
        # هذا يلتقط الأخطاء الأخرى مثل نقص الصلاحيات، لكن ping3 تحاول تفاديها
        return jsonify({
            "status": "error",
            "error": f"خطأ في تنفيذ Ping: {e}"
        }), 500
    except Exception as e:
        # لجميع الأخطاء غير المتوقعة الأخرى
        return jsonify({
            "status": "error",
            "error": f"خطأ غير متوقع في API: {e}"
        }), 500


@app.route('/', methods=['GET'])
def home():
    return "API Service is Running. Use /ping?host=<IP> for ICMP check."

if __name__ == '__main__':
    # تأكد من استخدام الإعدادات المناسبة لـ Render (PORT 5000)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
