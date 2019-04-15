var base = require('./base.js');
require('skulpt');
var CodeMirror = require('codemirror');
require('codemirror/mode/python/python.js');

var test_cases = {};

$(document).ready(function () {
    $('#run_code').click(function () {
        for (var id in test_cases) {
            if (test_cases.hasOwnProperty(id)) {
                var test_case = test_cases[id];
                test_case.received_output = '';
                test_case.is_error = false;
                test_case.test_input_list = test_case.test_input.split('\n');
            }
        }
        var user_code = editor.getValue();
        var passed = run_test_cases(user_code);
        base.ajax_request(
            'save_question_attempt',
            {
                user_input: user_code,
                question: question_id,
                passed_tests: passed,
            },
            function(result) {console.log(result);}
        );
    });

    var editor = CodeMirror.fromTextArea(document.getElementById("code"), {
        mode: {
            name: "python",
            version: 3,
            singleLineStringErrors: false
        },
        lineNumbers: true,
        textWrapping: false,
        styleActiveLine: true,
        autofocus: true,
        indentUnit: 4,
        viewportMargin: Infinity
    });

    for (let i = 0; i < test_cases_list.length; i++) {
        data = test_cases_list[i];
        test_cases[data.id] = data
    }
});


function update_test_case_status(test_case) {
    var test_case_id = test_case.id;

    var expected_output = test_case.expected_output;
    // Add trailing newline to expected output
    // TODO: Move to database step
    if (!expected_output.endsWith('\n')) {
        expected_output += '\n';
    }
    var success = (test_case.received_output === expected_output) && !test_case.is_error;

    // Update status cell
    var status_element = $('#test-case-' + test_case_id + '-status');
    var status_text = '';
    if (success) {
        status_text = 'Passed'
    } else {
        status_text = 'Failed'
    }
    status_element.text(status_text);

    // Update output cell
    var output_element = $('#test-case-' + test_case_id + '-output');
    output_element.text(test_case.received_output);
    if (test_case.is_error) {
        output_element.addClass('error')
    } else {
        output_element.removeClass('error')
    }

    // Update row
    var row_element = $('#test-case-' + test_case_id + '-row');
    if (success) {
        row_element.addClass('table-success');
        row_element.removeClass('table-danger');
    } else {
        row_element.addClass('table-danger');
        row_element.removeClass('table-success');
    }
    return success;
}

function run_test_cases(user_code) {
    var passed_all_tests = true;

    // Currently runs in sequential order.
    for (var id in test_cases) {
        if (test_cases.hasOwnProperty(id)) {
            var test_case = test_cases[id];
            run_python_code(user_code, test_case);
            var passed_test = update_test_case_status(test_case);
            passed_all_tests = passed_all_tests && passed_test;
        }
    }
    return passed_all_tests;
}

function run_python_code(user_code, test_case) {
    // Configure Skulpt for running Python code
    Sk.configure({
        // Setup Skulpt to read internal library files
        read: function (x) {
            if (Sk.builtinFiles === undefined || Sk.builtinFiles["files"][x] === undefined)
                throw "File not found: '" + x + "'";
            return Sk.builtinFiles["files"][x];
        },
        inputfun: function (str) {
            return test_case['test_input_list'].shift();
        },
        inputfunTakesPrompt: true,
        // Append print() statements for test case
        output: function(received_output) {
            test_case['received_output'] += received_output;
        },
        python3: true,
        execLimit: 1000,
    });
    if (typeof user_code == 'string' && user_code.trim()) {
        try {
            Sk.importMainWithBody("<stdin>", false, user_code, true);
        } catch (error) {
            if (error.constructor.sk$type) {
                test_case.received_output = error.toString();
                test_case.is_error = true;
            } else {
                throw error;
            }
        }
    } else {
        test_case.received_output = 'No Python code provided.';
        test_case.is_error = true;
    }
}
