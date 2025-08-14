#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الوكيل الهجين الخارق Pro - التطبيق الرئيسي
تطبيق Flask متقدم مع دعم WebSocket وميزات الذكاء الاصطناعي المتطورة
مع دعم كامل للمخرجات المهيكلة (Structured Output)
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time

# إضافة مسار المشروع إلى sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد الإعدادات والخدمات
from config.settings import Config
from src.core.super_hybrid_agent import SuperHybridAgent
from src.services.memory_service import MemoryService
from src.services.voice_service import VoiceService
from src.services.file_service import FileService
from src.utils.logger import setup_logger # هذا الاستيراد قد لا يكون ضرورياً إذا كنت تستخدم logging.basicConfig مباشرة
from src.utils.security import SecurityManager

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,  # تعيين مستوى التسجيل إلى INFO (أو DEBUG لرؤية المزيد)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # لإرسال السجلات إلى سطر الأوامر
    ]
)

# **تعريف كائن logger هنا ليصبح متاحاً في جميع أنحاء الملف**
logger = logging.getLogger(__name__)

class SuperHybridAgentApp:
    """التطبيق الرئيسي للوكيل الهجين الخارق"""
    
    def __init__(self):
        self.app = None
        self.socketio = None
        self.agent = None
        self.memory_service = None
        self.voice_service = None
        self.file_service = None
        self.security_manager = None
        self.active_sessions = {}
        self.system_stats = {
            'start_time': datetime.now(),
            'total_messages': 0,
            'total_tasks': 0,
            'active_sessions': 0
        }
        
        self.init_app()
    
    def init_app(self):
        """تهيئة تطبيق Flask والخدمات"""
        try:
            # إنشاء تطبيق Flask
            self.app = Flask(__name__)
            self.app.config.from_object(Config)
            
            # تهيئة الإعدادات
            Config.init_app(self.app)
            
            # تفعيل CORS
            CORS(self.app, origins="*")
            
            # تهيئة SocketIO
            self.socketio = SocketIO(
                self.app,
                cors_allowed_origins="*",
                async_mode='threading',
                logger=True,
                engineio_logger=True
            )
            
            # تهيئة الخدمات
            self.init_services()
            
            # تسجيل المسارات
            self.register_routes()
            
            # تسجيل أحداث WebSocket
            self.register_socket_events()
            
            logger.info("تم تهيئة التطبيق بنجاح")
            
        except Exception as e:
            logger.error(f"خطأ في تهيئة التطبيق: {str(e)}")
            raise
    
    def init_services(self):
        """تهيئة جميع الخدمات"""
        try:
            # خدمة الأمان
            self.security_manager = SecurityManager()
            
            # خدمة الذاكرة
            self.memory_service = MemoryService()
            
            # خدمة الصوت
            self.voice_service = VoiceService()
            
            # خدمة الملفات
            self.file_service = FileService()
            
            # الوكيل الهجين الرئيسي
            self.agent = SuperHybridAgent()
            
            logger.info("تم تهيئة جميع الخدمات بنجاح")
            
        except Exception as e:
            logger.error(f"خطأ في تهيئة الخدمات: {str(e)}")
            raise
    
    def register_routes(self):
        """تسجيل مسارات HTTP"""
        
        @self.app.route('/')
        def index():
            """الصفحة الرئيسية"""
            return render_template('index.html')
        
        @self.app.route('/api/health')
        def health_check():
            """فحص صحة النظام"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': str(datetime.now() - self.system_stats['start_time']),
                'stats': self.system_stats
            })
        
        @self.app.route('/api/stats')
        def get_stats():
            """إحصائيات النظام"""
            return jsonify({
                'system_stats': self.system_stats,
                'agent_stats': self.agent.get_stats() if self.agent else {},
                'memory_stats': self.memory_service.get_stats() if self.memory_service else {}
            })
        
        # ===== مسارات المخرجات المهيكلة =====
        
        @self.app.route('/api/structured/schemas', methods=['GET'])
        def get_available_schemas():
            """الحصول على المخططات المتاحة مع معلوماتها"""
            try:
                schemas_info = self.agent.get_available_schemas_info()
                return jsonify({
                    "success": True,
                    "schemas": schemas_info
                })
            except Exception as e:
                logger.error(f"خطأ في الحصول على المخططات: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/structured/process', methods=['POST'])
        def process_structured():
            """معالجة طلب مع مخرجات مهيكلة"""
            try:
                data = request.get_json()
                message = data.get('message', '')
                schema_name = data.get('schema', 'agent_response')
                persona = data.get('persona', 'hybrid')
                mode = data.get('mode', 'hybrid')
                session_id = data.get('session_id')
                
                if not message:
                    return jsonify({
                        "success": False,
                        "error": "الرسالة مطلوبة"
                    }), 400
                
                # تحديث إحصائيات الجلسة
                if session_id and session_id in self.active_sessions:
                    self.active_sessions[session_id]['message_count'] += 1
                    self.active_sessions[session_id]['last_activity'] = datetime.now()
                
                result = self.agent.process_with_structured_output(message, schema_name)
                
                # تحديث الإحصائيات العامة
                self.system_stats['total_messages'] += 1
                if result.get('success'):
                    self.system_stats['total_tasks'] += 1
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"خطأ في المعالجة المهيكلة: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/structured/smart-process', methods=['POST'])
        def smart_process():
            """معالجة ذكية مع اختيار تلقائي للمخطط"""
            try:
                data = request.get_json()
                message = data.get('message', '')
                persona = data.get('persona', 'hybrid')
                mode = data.get('mode', 'hybrid')
                session_id = data.get('session_id')
                
                if not message:
                    return jsonify({
                        "success": False,
                        "error": "الرسالة مطلوبة"
                    }), 400
                
                # تحديث إحصائيات الجلسة
                if session_id and session_id in self.active_sessions:
                    self.active_sessions[session_id]['message_count'] += 1
                    self.active_sessions[session_id]['last_activity'] = datetime.now()
                
                # تحليل الطلب واختيار أفضل مخطط
                analysis = self.agent.analyze_request_and_suggest_schema(message)
                suggested_schema = analysis.get('suggested_schema', 'agent_response')
                
                # معالجة مع المخطط المقترح
                result = self.agent.process_with_structured_output(message, suggested_schema)
                
                # إضافة معلومات التحليل للنتيجة
                result['analysis'] = analysis
                
                # تحديث الإحصائيات العامة
                self.system_stats['total_messages'] += 1
                if result.get('success'):
                    self.system_stats['total_tasks'] += 1
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"خطأ في المعالجة الذكية: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/structured/analyze', methods=['POST'])
        def analyze_request():
            """تحليل طلب واقتراح أفضل مخطط"""
            try:
                data = request.get_json()
                message = data.get('message', '')
                
                if not message:
                    return jsonify({
                        "success": False,
                        "error": "الرسالة مطلوبة"
                    }), 400
                
                analysis = self.agent.analyze_request_and_suggest_schema(message)
                
                return jsonify({
                    "success": True,
                    "analysis": analysis
                })
                
            except Exception as e:
                logger.error(f"خطأ في تحليل الطلب: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/structured/example/<schema_name>', methods=['GET'])
        def get_schema_example(schema_name):
            """الحصول على مثال لمخطط محدد"""
            try:
                example = self.agent.structured_output.get_schema_example(schema_name) # تم تصحيح اسم الدالة هنا
                if example:
                    return jsonify({
                        "success": True,
                        "example": example,
                        "schema_name": schema_name
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": f"مخطط غير موجود: {schema_name}"
                    }), 404
            except Exception as e:
                logger.error(f"خطأ في الحصول على مثال المخطط: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        # ===== باقي المسارات =====
        
        @self.app.route('/api/upload', methods=['POST'])
        def upload_file():
            """رفع الملفات"""
            try:
                if 'file' not in request.files:
                    return jsonify({'success': False, 'error': 'لم يتم العثور على ملف'})
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'success': False, 'error': 'لم يتم اختيار ملف'})
                
                result = self.file_service.upload_file(file)
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"خطأ في رفع الملف: {str(e)}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat_api():
            """API للمحادثة (محدث لدعم المخرجات المهيكلة)"""
            try:
                data = request.get_json()
                message = data.get('message', '')
                mode = data.get('mode', 'hybrid')
                persona = data.get('persona', 'hybrid')
                settings = data.get('settings', {})
                session_id = data.get('session_id')
                
                # دعم المخرجات المهيكلة
                use_structured = data.get('structured', False)
                schema_name = data.get('schema', 'agent_response')
                
                if not message:
                    return jsonify({'success': False, 'error': 'الرسالة فارغة'})
                
                # تحديث إحصائيات الجلسة
                if session_id and session_id in self.active_sessions:
                    self.active_sessions[session_id]['message_count'] += 1
                    self.active_sessions[session_id]['last_activity'] = datetime.now()
                
                if use_structured:
                    # استخدام المخرجات المهيكلة
                    response = self.agent.process_with_structured_output(message, schema_name)
                else:
                    # الطريقة العادية
                    response = self.agent.process_message(
                        message=message,
                        mode=mode,
                        persona=persona,
                        settings=settings
                        # session_id غير موجود في دالة process_message في SuperHybridAgent
                    )
                
                # تحديث الإحصائيات
                self.system_stats['total_messages'] += 1
                if response.get('task_completed') or response.get('success'):
                    self.system_stats['total_tasks'] += 1
                
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"خطأ في معالجة الرسالة: {str(e)}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/voice/synthesize', methods=['POST'])
        def synthesize_voice():
            """تحويل النص إلى كلام"""
            try:
                data = request.get_json()
                text = data.get('text', '')
                
                if not text:
                    return jsonify({'success': False, 'error': 'النص فارغ'})
                
                result = self.voice_service.text_to_speech(text)
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"خطأ في تحويل النص إلى كلام: {str(e)}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/memory/search', methods=['POST'])
        def search_memory():
            """البحث في الذاكرة"""
            try:
                data = request.get_json()
                query = data.get('query', '')
                
                if not query:
                    return jsonify({'success': False, 'error': 'استعلام البحث فارغ'})
                
                results = self.memory_service.search(query)
                return jsonify({'success': True, 'results': results})
                
            except Exception as e:
                logger.error(f"خطأ في البحث في الذاكرة: {str(e)}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'المسار غير موجود'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"خطأ داخلي في الخادم: {str(error)}")
            return jsonify({'error': 'خطأ داخلي في الخادم'}), 500
    
    def register_socket_events(self):
        """تسجيل أحداث WebSocket"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """اتصال عميل جديد"""
            session_id = request.sid
            self.active_sessions[session_id] = {
                'connected_at': datetime.now(),
                'message_count': 0,
                'last_activity': datetime.now()
            }
            self.system_stats['active_sessions'] = len(self.active_sessions)
            
            logger.info(f"عميل جديد متصل: {session_id}")
            emit('connection_status', {'status': 'connected', 'session_id': session_id})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """قطع اتصال العميل"""
            session_id = request.sid
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                self.system_stats['active_sessions'] = len(self.active_sessions)
            
            logger.info(f"تم قطع اتصال العميل: {session_id}")
        
        @self.socketio.on('send_message')
        def handle_message(data):
            """معالجة رسالة من العميل (محدث لدعم المخرجات المهيكلة)"""
            try:
                session_id = request.sid
                message = data.get('message', '')
                mode = data.get('mode', 'hybrid')
                persona = data.get('persona', 'hybrid')
                settings = data.get('settings', {})
                
                # دعم المخرجات المهيكلة
                use_structured = data.get('structured', False)
                schema_name = data.get('schema', 'agent_response')
                
                if not message:
                    emit('error', {'message': 'الرسالة فارغة'})
                    return
                
                # تحديث نشاط الجلسة
                if session_id in self.active_sessions:
                    self.active_sessions[session_id]['message_count'] += 1
                    self.active_sessions[session_id]['last_activity'] = datetime.now()
                
                # إرسال إشارة بدء الكتابة
                emit('typing_start')
                
                # معالجة الرسالة في خيط منفصل
                def process_message_async():
                    try:
                        if use_structured:
                            # استخدام المخرجات المهيكلة
                            response = self.agent.process_with_structured_output(message, schema_name)
                        else:
                            # الطريقة العادية
                            response = self.agent.process_message(
                                message=message,
                                mode=mode,
                                persona=persona,
                                settings=settings,
                                # session_id غير موجود في دالة process_message في SuperHybridAgent
                            )
                        
                        # تحديث الإحصائيات
                        self.system_stats['total_messages'] += 1
                        if response.get('task_completed') or response.get('success'):
                            self.system_stats['total_tasks'] += 1
                        
                        # إرسال الاستجابة
                        self.socketio.emit('typing_stop', room=session_id)
                        self.socketio.emit('message_response', response, room=session_id)
                        
                    except Exception as e:
                        logger.error(f"خطأ في معالجة الرسالة: {str(e)}")
                        self.socketio.emit('typing_stop', room=session_id)
                        self.socketio.emit('error', {'message': str(e)}, room=session_id)
                
                # تشغيل المعالجة في خيط منفصل
                thread = threading.Thread(target=process_message_async)
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                logger.error(f"خطأ في معالجة رسالة WebSocket: {str(e)}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('update_model')
        def handle_model_update(data):
            """تحديث النموذج المستخدم"""
            try:
                model = data.get('model')
                if model:
                    self.agent.update_model(model)
                    emit('model_updated', {'model': model})
                    logger.info(f"تم تحديث النموذج إلى: {model}")
                
            except Exception as e:
                logger.error(f"خطأ في تحديث النموذج: {str(e)}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('get_session_info')
        def handle_session_info():
            """الحصول على معلومات الجلسة"""
            session_id = request.sid
            session_info = self.active_sessions.get(session_id, {})
            emit('session_info', session_info)
        
        @self.socketio.on('get_schemas')
        def handle_get_schemas():
            """الحصول على المخططات المتاحة عبر WebSocket"""
            try:
                schemas_info = self.agent.get_available_schemas_info()
                emit('schemas_list', {'success': True, 'schemas': schemas_info})
            except Exception as e:
                logger.error(f"خطأ في الحصول على المخططات: {str(e)}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('analyze_message')
        def handle_analyze_message(data):
            """تحليل رسالة واقتراح مخطط عبر WebSocket"""
            try:
                message = data.get('message', '')
                if not message:
                    emit('error', {'message': 'الرسالة فارغة'})
                    return
                
                analysis = self.agent.analyze_request_and_suggest_schema(message)
                emit('message_analysis', {'success': True, 'analysis': analysis})
                
            except Exception as e:
                logger.error(f"خطأ في تحليل الرسالة: {str(e)}")
                emit('error', {'message': str(e)})
    
    def start_background_tasks(self):
        """بدء المهام الخلفية"""
        def cleanup_inactive_sessions():
            """تنظيف الجلسات غير النشطة"""
            while True:
                try:
                    current_time = datetime.now()
                    inactive_sessions = []
                    
                    for session_id, session_data in self.active_sessions.items():
                        last_activity = session_data.get('last_activity', current_time)
                        if (current_time - last_activity).total_seconds() > 3600:  # ساعة واحدة
                            inactive_sessions.append(session_id)
                    
                    for session_id in inactive_sessions:
                        del self.active_sessions[session_id]
                        logger.info(f"تم حذف الجلسة غير النشطة: {session_id}")
                    
                    self.system_stats['active_sessions'] = len(self.active_sessions)
                    
                except Exception as e:
                    logger.error(f"خطأ في تنظيف الجلسات: {str(e)}")
                
                time.sleep(300)  # كل 5 دقائق
        
        def update_system_stats():
            """تحديث إحصائيات النظام"""
            while True:
                try:
                    # تحديث إحصائيات الذاكرة والأداء
                    if self.memory_service:
                        self.memory_service.update_stats()
                    
                    if self.agent:
                        self.agent.update_stats()
                    
                except Exception as e:
                    logger.error(f"خطأ في تحديث الإحصائيات: {str(e)}")
                
                time.sleep(60)  # كل دقيقة
        
        # بدء المهام الخلفية
        cleanup_thread = threading.Thread(target=cleanup_inactive_sessions)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        stats_thread = threading.Thread(target=update_system_stats)
        stats_thread.daemon = True
        stats_thread.start()
        
        logger.info("تم بدء المهام الخلفية")
    
    def run(self, host=None, port=None, debug=None):
        """تشغيل التطبيق"""
        try:
            # بدء المهام الخلفية
            self.start_background_tasks()
            
            # إعدادات التشغيل
            host = host or Config.HOST
            port = port or Config.PORT
            debug = debug if debug is not None else Config.DEBUG
            
            logger.info(f"🚀 بدء تشغيل الوكيل الهجين الخارق Pro...")
            logger.info(f"📡 الخادم سيعمل على: http://{host}:{port}"  )
            logger.info(f"🎨 الواجهة المتقدمة مع المخرجات المهيكلة جاهزة!")
            logger.info("=" * 50)
            
            # تشغيل الخادم
            self.socketio.run(
                self.app,
                host=host,
                port=port,
                debug=debug,
                allow_unsafe_werkzeug=True
            )
            
        except Exception as e:
            logger.error(f"خطأ في تشغيل التطبيق: {str(e)}")
            raise

def create_app():
    """إنشاء تطبيق Flask"""
    app_instance = SuperHybridAgentApp()
    return app_instance.app, app_instance.socketio

def main():
    """الدالة الرئيسية"""
    try:
        # إنشاء وتشغيل التطبيق
        app_instance = SuperHybridAgentApp()
        app_instance.run()
        
    except KeyboardInterrupt:
        logger.info("تم إيقاف التطبيق بواسطة المستخدم")
    except Exception as e:
        logger.error(f"خطأ في تشغيل التطبيق: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
