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
    var top_element = $('#user-code-lines');
    code = traverse_code_container(top_element, indent, true);
    return code;
}

function traverse_code_container(container, indent, is_top) {
    var container_code = '';
    var lines = container.children('.parsons-draggable-line');
    if (lines.length > 0) {
        if (!is_top) {
            indent += indent_increment;
        }
        lines.each(function() {
            var line = $(this);
            var line_code = line.children('.parsons-line-content').text().trim();
            container_code += indent + line_code + '\n';
            var line_container = line.children('.parsons-drag-container');
            container_code += traverse_code_container(line_container, indent, false);
        });
        if (!is_top) {
            indent = indent.substring(0, indent_increment.length);
        }
    }
    return container_code;
}
