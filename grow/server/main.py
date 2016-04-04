import logging
import os
import jinja2
import re
import sys
import traceback
import urllib
import webob

# Allows "import grow" and "from grow import <name>".
sys.path.extend([os.path.join(os.path.dirname(__file__), '..', '..')])

from grow.common import sdk_utils
from grow.common import utils
from grow.pods import errors
from grow.pods import storage
from protorpc.wsgi import service
from werkzeug import exceptions
from werkzeug import routing
from werkzeug import utils as werkzeug_utils
from werkzeug import wrappers
from werkzeug import wsgi


_root = os.path.join(utils.get_grow_dir(), 'server', 'templates')
_loader = storage.FileStorage.JinjaLoader(_root)
_env = jinja2.Environment(
    loader=_loader,
    autoescape=True,
    trim_blocks=True,
    extensions=[
        'jinja2.ext.autoescape',
        'jinja2.ext.do',
        'jinja2.ext.i18n',
        'jinja2.ext.loopcontrols',
        'jinja2.ext.with_',
    ])


def serve_console(pod, request, values):
    kwargs = {'pod': pod}
    values_to_templates = {
        'content': 'collections.html',
        'translations': 'catalogs.html',
    }
    value = values.get('page')
    template_path = values_to_templates.get(value, 'main.html')
    if value == 'translations' and values.get('locale'):
        kwargs['locale'] = values.get('locale')
        template_path = 'catalog.html'
    template = _env.get_template(template_path)
    content = template.render(kwargs)
    response = wrappers.Response(content)
    response.headers['Content-Type'] = 'text/html'
    return response


def serve_pod(pod, request, values):
    path = urllib.unquote(request.path)  # Support escaped paths.
    controller, params = pod.routes.match(path, request.environ)
    controller.validate(params)
    headers = controller.get_http_headers(params)
    request_etag = request.headers.get('If-None-Match')
    if 'ETag' in headers and request_etag == headers['ETag']:
        response = wrappers.Response(headers=headers, status=304)
        return response
    if 'X-AppEngine-BlobKey' in headers:
        return wrappers.Response(headers=headers)
    content = controller.render(params)
    response = wrappers.Response(content, headers=headers)
    return response


class PodServer(object):

    def __init__(self, pod, debug=False):
        rule = routing.Rule
        self.pod = pod
        self.debug = debug
        self.url_map = routing.Map([
            rule('/', endpoint=serve_pod),
            rule('/_grow/<any("translations"):page>/<path:locale>', endpoint=serve_console),
            rule('/_grow/<path:page>', endpoint=serve_console),
            rule('/_grow', endpoint=serve_console),
            rule('/<path:path>', endpoint=serve_pod),
        ], strict_slashes=False)

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return endpoint(self.pod, request, values)
        except routing.RequestRedirect as e:
            return werkzeug_utils.redirect(e.new_url)
        except Exception as e:
            return self.handle_exception(request, e)

    def wsgi_app(self, environ, start_response):
        request = wrappers.Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def handle_exception(self, request, exc):
        log = logging.exception if self.debug else self.pod.logger.error
        if isinstance(exc, webob.exc.HTTPException):
            status = exc.status_int
            log('{}: {}'.format(status, request.path))
        else:
            status = 500
            log('{}: {} - {}'.format(status, request.path, exc))
        template = _env.get_template('error.html')
        if (isinstance(exc, errors.BuildError)):
            tb = exc.traceback
        else:
            unused_error_type, unused_value, tb = sys.exc_info()
        formatted_traceback = [
            re.sub('^  ', '', line)
            for line in traceback.format_tb(tb)]
        formatted_traceback = '\n'.join(formatted_traceback)
        kwargs = {
            'exception': exc,
            'is_web_exception': isinstance(exc, webob.exc.HTTPException),
            'pod': self.pod,
            'status': status,
            'traceback': formatted_traceback,
        }
        try:
            home_doc = self.pod.get_home_doc()
            if home_doc:
                kwargs['home_url'] = home_doc.url.path
        except:
            pass
        if (isinstance(exc, errors.BuildError)):
            kwargs['build_error'] = exc.exception
        if (isinstance(exc, errors.BuildError)
           and isinstance(exc.exception, jinja2.TemplateSyntaxError)):
            kwargs['template_exception'] = exc.exception
        elif isinstance(exc, jinja2.TemplateSyntaxError):
            kwargs['template_exception'] = exc
        content = template.render(**kwargs)
        response = wrappers.Response(content, status=status)
        response.headers['Content-Type'] = 'text/html'
        return response


def create_wsgi_app(pod, debug=False):
    podserver_app = PodServer(pod, debug=debug)
    static_path = os.path.join(utils.get_grow_dir(), 'server', 'frontend')
    return wsgi.SharedDataMiddleware(podserver_app, {
        '/_grow/static': static_path,
    })
