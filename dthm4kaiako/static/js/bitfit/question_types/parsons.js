var base = require('./base.js');
var Sortable = require('sortablejs');
require('skulpt');

var test_cases = {};
var indent_increment = '    ';

$(document).ready(function(){
    var all_sortables = document.getElementsByClassName('parsons-drag-container');
    Array.prototype.forEach.call(all_sortables, function (element) {
        new Sortable(element, {
            group: 'parsons', // set both lists to same group
            animation: 150,
            swapThreshold: 0.5,
            fallbackOnBody: true
        });
    });

    $('#run_code').click(function () {
        for (var id in test_cases) {
            if (test_cases.hasOwnProperty(id)) {
                var test_case = test_cases[id];
                test_case.received_output = '';
                test_case.is_error = false;
            }
        }
        var user_code = get_user_code();
        // var passed = run_test_cases(user_code);
        // base.ajax_request(
        //     'save_question_attempt',
        //     {
        //         user_input: user_code,
        //         question: question_id,
        //         passed_tests: passed,
        //     },
        //     function (result) { console.log(result); }
        // );
    });
});

function get_user_code() {
    var indent = '';
    var code = '';
    var top_element = document.getElementById('user-code-lines');
    code = traverse_line(top_element, code, indent);
    return code;
}

function traverse_line(line, code, indent) {
    code += indent + line.childNodes[0].nodeValue.trim() + '\n';
    var children = $(line).children();
    if (children.length > 0) {
        indent += indent_increment;
        children.each(function(){
            code = traverse_line(this, code, indent);
        });
        indent -= indent_increment;
    }
    return code;
}
