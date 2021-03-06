import pytest
from wes.main import clone_update_repo
from wes.framework_plugins.common import JavaProcessor
from wes.framework_plugins.plugin_javaservlet import CustomFramework
import os
import javalang

@pytest.fixture(scope="module")
def plugin(tmpdir_factory):
    # Setup the object by cloning WEST and creating instance of JavaProcessor
    working_dir = str(tmpdir_factory.getbasetemp())
    project = {'base_url': 'http://west.example.com/', 'git_repo': 'git@github.com:indeedsecurity/WEST.git'}
    project_repo_path = project['git_repo'].split(':')[-1][:-4]
    project_name = project['git_repo'].split('/')[-1][:-4]
    product_group = project_repo_path.split('/')[0]

    group_folder = os.path.join(working_dir, product_group)
    project_folder = os.path.join(group_folder, project_name)

    # clone/update the repositories
    clone_update_repo(project_folder, project['git_repo'])

    processors = {
        'java': JavaProcessor(working_dir=project_folder)
    }
    processors['java'].load_project()

    return CustomFramework(working_dir=os.path.abspath(project_folder), processors=processors)

def test_identify(plugin, mocker):
    assert plugin.identify() == True
    mocker.patch('glob.glob', return_value=[])
    assert plugin.identify() == False

def test_find_endpoints(plugin):
    # The only real way to test this method is with an integration test because
    # it basically integrates all of the method within the class
    endpoints = plugin.find_endpoints()
    assert type(endpoints) is list
    for ep in endpoints:
        # Check that each endpoint has the required key value types
        assert type(ep) is dict
        assert 'templates' in ep
        assert 'endpoints' in ep
        assert 'methods' in ep
        assert 'filepath' in ep
        assert 'params' in ep
        assert type(ep['templates']) is set
        assert type(ep['endpoints']) is set
        assert type(ep['methods']) is list
        assert type(ep['templates']) is set
        assert type(ep['filepath']) is str
        assert type(ep['params']) is list

def test_find_endpoints_bad_web_xml(plugin, mocker):
    mocker.patch('wes.framework_plugins.plugin_javaservlet.CustomFramework._find_web_xml', return_value=None)
    mocker.patch('wes.framework_plugins.plugin_javaservlet.CustomFramework._find_servlet_classes', return_value=None)

    assert plugin.find_endpoints() == []

def test_find_web_xml(plugin, mocker):
    mocker.patch('glob.glob', return_value=['testing'])
    assert plugin._find_web_xml() == 'testing'

def test_find_web_xml_bad(plugin, mocker):
    mocker.patch('glob.glob', return_value=[])
    assert plugin._find_web_xml() == None

def test_find_servlet_classes(plugin, mocker):
    mocker.patch('wes.framework_plugins.plugin_javaservlet.CustomFramework._load_xml')
    try:
        import lxml.etree as ET
    except ImportError:
        import xml.etree.ElementTree as ET

    plugin.root_element = ET.XML("""
<?xml version="1.0" encoding="ISO-8859-1"?>
<web-app xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://java.sun.com/xml/ns/javaee" xmlns:jsp="http://java.sun.com/xml/ns/javaee/jsp" xsi:schemaLocation="http://java.sun.com/xml/ns/javaee http://java.sun.com/xml/ns/javaee/web-app_3_0.xsd" version="3.0">
  <display-name>WEST</display-name>
  <servlet>
    <servlet-name>spring</servlet-name>
    <servlet-class>org.springframework.web.servlet.DispatcherServlet</servlet-class>
    <load-on-startup>1</load-on-startup>
  </servlet>
  <servlet>
    <servlet-name>MYTESTSERVLET</servlet-name>
    <servlet-class>com.indeed.security.wes.MYTESTCLASS</servlet-class>
  </servlet>
  <servlet>
    <servlet-name>MYTESTJSP</servlet-name>
    <jsp-file>MYJSP.jsp</jsp-file>
  </servlet>
  <servlet-mapping>
    <servlet-name>spring</servlet-name>
    <url-pattern>/</url-pattern>
  </servlet-mapping>
  <servlet-mapping>
    <servlet-name>MYTESTSERVLET</servlet-name>
    <url-pattern>/TESTPATH</url-pattern>
  </servlet-mapping>
  <servlet-mapping>
    <servlet-name>MYTESTJSP</servlet-name>
    <url-pattern>/TESTJSP</url-pattern>
  </servlet-mapping>
</web-app>
""".strip().encode('ascii', errors='backslashreplace'))
    plugin.namespace = plugin.root_element.nsmap[None]

    assert plugin._find_servlet_classes("") == [
        {'class': 'org.springframework.web.servlet.DispatcherServlet', 'name': 'spring'},
        {'class': 'com.indeed.security.wes.MYTESTCLASS', 'name': 'MYTESTSERVLET'},
        {'name': 'MYTESTJSP', 'templates': 'MYJSP.jsp'}
    ]

def test_find_servlet_classes_bad(plugin, mocker):
    mocker.patch('wes.framework_plugins.plugin_javaservlet.CustomFramework._load_xml')

    plugin.root_element = None

    assert plugin._find_servlet_classes("") == None

def test_find_path_for_servlet(plugin, mocker):
    mocker.patch('wes.framework_plugins.plugin_javaservlet.CustomFramework._load_xml')
    try:
        import lxml.etree as ET
    except ImportError:
        import xml.etree.ElementTree as ET

    plugin.root_element = ET.XML("""
<?xml version="1.0" encoding="ISO-8859-1"?>
<web-app xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://java.sun.com/xml/ns/javaee" xmlns:jsp="http://java.sun.com/xml/ns/javaee/jsp" xsi:schemaLocation="http://java.sun.com/xml/ns/javaee http://java.sun.com/xml/ns/javaee/web-app_3_0.xsd" version="3.0">
  <display-name>WEST</display-name>
  <servlet>
    <servlet-name>spring</servlet-name>
    <servlet-class>org.springframework.web.servlet.DispatcherServlet</servlet-class>
    <load-on-startup>1</load-on-startup>
  </servlet>
  <servlet>
    <servlet-name>MYTESTSERVLET</servlet-name>
    <servlet-class>com.indeed.security.wes.MYTESTCLASS</servlet-class>
  </servlet>
  <servlet>
    <servlet-name>MYTESTJSP</servlet-name>
    <jsp-file>MYJSP.jsp</jsp-file>
  </servlet>
  <servlet-mapping>
    <servlet-name>spring</servlet-name>
    <url-pattern>/</url-pattern>
  </servlet-mapping>
  <servlet-mapping>
    <servlet-name>MYTESTSERVLET</servlet-name>
    <url-pattern>/TESTPATH</url-pattern>
  </servlet-mapping>
  <servlet-mapping>
    <servlet-name>MYTESTJSP</servlet-name>
    <url-pattern>/TESTJSP</url-pattern>
  </servlet-mapping>
</web-app>
""".strip().encode('ascii', errors='backslashreplace'))
    plugin.namespace = plugin.root_element.nsmap[None]

    assert plugin._find_path_for_servlet("", "") == None
    assert plugin._find_path_for_servlet("", "spring") == set(["/"])
    assert plugin._find_path_for_servlet("", "MYTESTSERVLET") == set(["/TESTPATH"])
    assert plugin._find_path_for_servlet("", "MYTESTJSP") == set(["/TESTJSP"])

def test_find_path_for_servlet_bad(plugin, mocker):
    mocker.patch('wes.framework_plugins.plugin_javaservlet.CustomFramework._load_xml')

    plugin.root_element = None

    assert plugin._find_path_for_servlet("", "") == None

def test_is_spring_servlet_dipatcher_or_external_first(plugin, mocker):
    mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('wes.framework_plugins.plugin_javaservlet.CustomFramework._find_class_file_path')
    mocker.patch('codecs.open', mocker.mock_open(read_data="class WesDispatcherServlet extends DispatcherServlet{}"))

    assert plugin._is_spring_servlet_dipatcher_or_external('') == True

def test_is_spring_servlet_dipatcher_or_external_second(plugin, mocker):
    mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('wes.framework_plugins.plugin_javaservlet.CustomFramework._find_class_file_path')
    mocker.patch('codecs.open', mocker.mock_open(read_data="Test String"))

    assert plugin._is_spring_servlet_dipatcher_or_external('') == False

def test_is_spring_servlet_dipatcher_or_external_third(plugin, mocker):
    mocker.patch('os.path.isfile', return_value=False)
    mocker.patch('wes.framework_plugins.plugin_javaservlet.CustomFramework._find_class_file_path')

    assert plugin._is_spring_servlet_dipatcher_or_external('') == True

def test_find_class_file_path(plugin, mocker):
    mocker.patch('os.path.isfile', return_value=True)
    mocker.patch(
        'wes.framework_plugins.common.JavaProcessor.find_code_base_dir',
        return_value='/myCodeBaseDir/'
    )

    assert plugin._find_class_file_path('com.indeed.security.wes.MYTESTCLASS') == '/myCodeBaseDir/com/indeed/security/wes/MYTESTCLASS.java'

def test_find_request_get_param(plugin):
    plugin.processor.java_compilation_units['test_file'] = javalang.parse.parse(
    """
package com.indeed.security.wes.west.servlets;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class JSTEST extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        String a = request.getParameter("a");
        String b = request.getParameter("b");
    }
}
    """)

    endpoint = {
        'filepath': 'test_file',
        'params': []
    }

    assert plugin._find_request_get_param(endpoint) == {
        'filepath': 'test_file',
        'params': [{'filepath': 'test_file', 'line_number': 11, 'name': 'a'},
                   {'filepath': 'test_file', 'line_number': 12, 'name': 'b'}]
    }

def test_find_request_get_param_member(plugin):
    plugin.processor.java_compilation_units['test_file'] = javalang.parse.parse(
    """
package com.indeed.security.wes.west.servlets;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class JSTEST extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        String paramName = "a";
        String a = request.getParameter(paramName);
    }
}
    """)

    # Just processing the literals for this example. This is normally done for you automatically.
    plugin.processor.variable_lookup_table.update(
        plugin.processor._preprocess_java_literals(plugin.processor.java_compilation_units['test_file']))

    endpoint = {
        'filepath': 'test_file',
        'params': []
    }

    assert plugin._find_request_get_param(endpoint) == {
        'filepath': 'test_file',
        'params': [{'filepath': 'test_file', 'line_number': 12, 'name': 'a'}]
    }

def test_find_referenced_jsps(plugin):
    plugin.processor.java_compilation_units['test_file2'] = javalang.parse.parse(
    """
package com.indeed.security.wes.west.servlets;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class JSTEST extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.getRequestDispatcher("/WEB-INF/jsp/servlets/test.jsp").forward(request, response);
    }
}
    """)

    endpoint = {
        'filepath': 'test_file2'
    }
    assert 'java/src/main/webapp/WEB-INF/jsp/servlets/test.jsp' in plugin._find_referenced_jsps(endpoint)['templates']

def test_find_referenced_jsps_member(plugin):
    plugin.processor.java_compilation_units['test_file3'] = javalang.parse.parse(
    """
package com.indeed.security.wes.west.servlets;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class JSTEST extends HttpServlet {

    private final String MY_TEST_VIEW = "/WEB-INF/jsp/servlets/test.jsp";

    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.getRequestDispatcher(MY_TEST_VIEW).forward(request, response);
    }
}
    """)
    # Just processing the literals for this example. This is normally done for you automatically.
    plugin.processor.variable_lookup_table.update(plugin.processor._preprocess_java_literals(plugin.processor.java_compilation_units['test_file3']))

    endpoint = {
        'filepath': 'test_file3'
    }

    assert 'java/src/main/webapp/WEB-INF/jsp/servlets/test.jsp' in plugin._find_referenced_jsps(endpoint)['templates']

def test_find_referenced_jsps_with_templates(plugin):
    plugin.processor.java_compilation_units['test_file4'] = javalang.parse.parse(
    """
package com.indeed.security.wes.west.servlets;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class JSTEST extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.getRequestDispatcher("/WEB-INF/jsp/servlets/test.jsp").forward(request, response);
    }
}
    """)

    endpoint = {
        'filepath': 'test_file4',
        'templates': ['java/src/main/webapp/one', 'two']
    }
    resulting_endpoint = plugin._find_referenced_jsps(endpoint)
    assert 'java/src/main/webapp/WEB-INF/jsp/servlets/test.jsp' in resulting_endpoint['templates']
    assert 'java/src/main/webapp/one' in resulting_endpoint['templates']
    assert 'java/src/main/webapp/two' in resulting_endpoint['templates']

def test_find_jsp_params(plugin, mocker):
    # Not going to test this here because it's already tested elsewhere
    mocker.patch('wes.framework_plugins.common.JavaProcessor.get_jsp_params',
                 return_value=['1a', '2b', '3c'])

    endpoint = {
        'templates': ['java/src/main/webapp/WEB-INF/jsp/servlets/test.jsp',
                      'java/src/main/webapp/WEB-INF/jsp/servlets/test1.jsp'],
        'params': []
    }

    assert [{'filepath': 'WEB-INF/jsp/servlets/test.jsp', 'name': '1a'},
            {'filepath': 'WEB-INF/jsp/servlets/test.jsp', 'name': '2b'},
            {'filepath': 'WEB-INF/jsp/servlets/test.jsp', 'name': '3c'},
            {'filepath': 'WEB-INF/jsp/servlets/test1.jsp', 'name': '1a'},
            {'filepath': 'WEB-INF/jsp/servlets/test1.jsp', 'name': '2b'},
            {'filepath': 'WEB-INF/jsp/servlets/test1.jsp', 'name': '3c'}] == plugin._find_jsp_params(endpoint)['params']

def test_find_methods_for_endpoint(plugin):
    plugin.processor.java_compilation_units['test_file5'] = javalang.parse.parse(
    """
package com.indeed.security.wes.west.servlets;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class JSTEST extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        request.getRequestDispatcher("/WEB-INF/jsp/servlets/test.jsp").forward(request, response);
    }
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        doGet(request, response);
    }
    protected void doDelete(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        doGet(request, response);
    }
    protected void doHead(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        doGet(request, response);
    }
    protected void doOptions(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        doGet(request, response);
    }
    protected void doPut(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        doGet(request, response);
    }
    protected void doTrace(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        doGet(request, response);
    }
}
    """)

    endpoint = {
        'filepath': 'test_file5',
        'methods': set()
    }
    methods = set(['GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS', 'PUT', 'TRACE'])
    assert methods == plugin._find_methods_for_endpoint(endpoint)['methods']

def test_convert_endpoint_to_python_regex(plugin):
    assert 'mypath/[^/]*' == plugin._convert_endpoint_to_python_regex('mypath/*')
    assert 'mypath/path' == plugin._convert_endpoint_to_python_regex('mypath/path')
    assert 'mypath/[^/]*/testing' == plugin._convert_endpoint_to_python_regex('mypath/*/testing')

def test_clean_endpoints(plugin):
    endpoints = [
        {
            'endpoints': set(['test/path/*', 'profile']),
            'params': set(['test1', 'test2']),
            'methods': set(['POST', 'GET']),
            'testKey': None
        },
        {
            'params': set(['test1', 'test2'])
        }
    ]
    expected_endpoints = [
        {
            'endpoints': set(['test/path/[^/]*', 'profile']),
            'params': set(['test1', 'test2']),
            'methods': set(['POST', 'GET']),
        }
    ]
    assert plugin._clean_endpoints(endpoints) == expected_endpoints
