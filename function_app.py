import os

import azure.functions as func

from app.handlers import api_handler, reconcile_handler, worker_handler

app = func.FunctionApp()
role = os.environ.get('APP_ROLE')
if role == 'api':
    @app.route(route='{*path}', methods=['GET', 'POST'], auth_level=func.AuthLevel.ANONYMOUS)
    def api(req: func.HttpRequest) -> func.HttpResponse:
        body, status, headers = api_handler(req)
        return func.HttpResponse(body, status_code=status, headers=headers)
elif role == 'worker':
    @app.queue_trigger(arg_name='message', queue_name='jobs', connection='JobQueue')
    def dispatch(message: func.QueueMessage):
        worker_handler(message.get_body())

    @app.timer_trigger(arg_name='timer', schedule='0 * * * * *', run_on_startup=False, use_monitor=True)
    def reconcile(timer: func.TimerRequest):
        reconcile_handler()
else:
    raise RuntimeError('APP_ROLE must be api or worker')
