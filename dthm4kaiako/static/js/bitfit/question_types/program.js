require('./base.js');
require('skulpt');
var CodeMirror = require('codemirror');
require('codemirror/mode/python/python.js');

$(document).ready(function () {
    $('#run_code').click(function () {
        for (var id in test_cases) {
            if (test_cases.hasOwnProperty(id)) {
                var test_case = test_cases[id];
                test_case['received_output'] = '';
                test_case['test_input_list'] = test_case['test_input'].split('\n');
            }
        }
        var user_code = editor.getValue();
        run_test_cases(user_code);
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

    var output_element = $('#test-case-' + test_case_id + '-output');
    output_element.text(test_case.received_output);

    var expected_output = test_case.expected_output;
    // Add trailing newline to expected output
    // TODO: Move to database step
    if (!expected_output.endsWith('\n')) {
        expected_output += '\n';
    }
    var success = test_case.received_output === expected_output;

    // Update status element
    var status_element = $('#test-case-' + test_case_id + '-status');
    var status_text = '';
    if (success) {
        status_text = 'Passed'
    } else {
        status_text = 'Failed'
    }
    status_element.text(status_text);

    // Update row element
    var row_element = $('#test-case-' + test_case_id + '-row');
    if (success) {
        row_element.addClass('table-success');
        row_element.removeClass('table-danger');
    } else {
        row_element.addClass('table-danger');
        row_element.removeClass('table-success');
    }
}

function run_test_cases(user_code) {
    // Currently runs in sequential order.
    for (var id in test_cases) {
        if (test_cases.hasOwnProperty(id)) {
            var test_case = test_cases[id];
            run_python_code(user_code, test_case);
            update_test_case_status(test_case);
        }
    }
}

function run_python_code(user_code, test_case) {
    document.getElementById("output").innerHTML = "";
    document.getElementById("error-output").innerHTML = "";
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
        python3: true
    });
    if (typeof user_code == 'string' && user_code.trim()) {
        try {
            Sk.importMainWithBody("<stdin>", false, user_code, true);
        // TODO: Only catch Python errors
        } catch (error) {
            document.getElementById("error-output").innerHTML = error.toString();
        }
    } else {
        throw new Error('No Python code provided.')
    }
}

// var hide_results = function() {
//     $('#result-table').addClass('hidden');
//     $('#credit').addClass('hidden');
//     $('#error').addClass('hidden');
//     $('#all-correct').addClass('hidden');
//     $('#has_saved').addClass('hidden');
//     $('.program-type-analysis').removeClass('hidden');
//     $('.function-type-analysis').removeClass('hidden');
// }

// var show_save_icon = function(result) {
//     $('#has_saved').removeClass('hidden');
//     setTimeout(() => {$('#has_saved').addClass('hidden')}, 2000);
// }

// var display_table = function(result) {
//     var output = JSON.parse(result.output.slice(0, -1));
//     var got_output_array = output["printed"];
//     var got_return_array = output["returned"];
//     var correctness_array = output["correct"];

//     var all_correct = true;
//     var has_print_contents = false;
//     var has_return_contents = false;
//     var tick = "https://png.icons8.com/color/50/000000/ok.png";
//     var cross = "https://png.icons8.com/color/50/000000/close-window.png";

//     for (var i = 0; i < correctness_array.length; i++) {
//         if (correctness_array[i] == false) {
//             all_correct = false;
//             $("#correctness-img" + i).attr("src", cross);
//         } else {
//             $("#correctness-img" + i).attr("src", tick);
//         }
//         if (got_output_array[i] && got_output_array[i].length > 0) {
//             has_print_contents = true;
//             $("#program-got" + i).html(got_output_array[i]);
//         }
//         console.log(got_return_array);
//         if (got_return_array[i] && is_func) {
//             has_return_contents = true;
//             $("#function-got" + i).html(got_return_array[i]);
//         }
//     }

//     $('#result-table').removeClass('hidden');
//     $('#credit').removeClass('hidden');

//     var user_input = editor.getValue();
//     if (all_correct) {
//         $('#all-correct').removeClass('hidden');
//         save_code(user_input, true, false, show_save_icon);
//     } else {
//         save_code(user_input, false, false, show_save_icon);
//     }
//     if (!has_print_contents) {
//         $(".program-type-analysis").addClass('hidden');
//     }
//     if (!has_return_contents) {
//         $(".function-type-analysis").addClass('hidden');
//     }
// }

// var display_results = function(result) {
//     $('#loading').addClass('hidden');
//     var user_input = editor.getValue();

//     if (result.output.length > 0) {
//         display_table(result);
//     }
//     if (result.stderr.length > 0) {
//         $('#error').text(result.stderr);
//         $('#error').removeClass('hidden');
//         save_code(user_input, false, false, show_save_icon);
//     }
//     if (result.cmpinfo.length > 0) {
//         $('#error').text(result.cmpinfo);
//         $('#error').removeClass('hidden');
//         save_code(user_input, false, false, show_save_icon);
//     }
// }

// $("#submit").click(function () {
//     var user_input = editor.getValue();

//     var data = {
//         user_input: user_input,
//         question: question_id
//     }
//     post('send_code', data, function (result) {
//         if (result.error) {
//             $('#error').text(result.error);
//             $('#error').removeClass('hidden');
//         } else {
//             var submission_id = result.id;
//             console.log(submission_id);
//             $('#loading').removeClass('hidden');
//             hide_results();
//             poll_until_completed(submission_id, display_results);
//         }
//     });
// });

// $('#save').click(function () {
//     var user_input = editor.getValue();
//     save_code(user_input, false, true, show_save_icon);
// });

// $('#show_solution').click(function () {
//     $('#solution').html(solution);
//     $('#show_solution').addClass('hidden');
// });
