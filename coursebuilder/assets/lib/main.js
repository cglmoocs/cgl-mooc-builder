$(document).ready(function() {
    /* CGL-MOOC-Builder:
     * Check user's inputs before submitting the form on registration page(register.html) */
    $("#register_button").live("click", function(event) {
        // Highlight the empty input box if it is required
        $(".required[value = '']").addClass('red-border');
        $(".required[value != '']").removeClass('red-border');
        // Check if Age input is an integer
        if(validate('', 'age', $("#age").val()) && $(".red-border").length == 0)
            return true;
        else {
            event.preventDefault();
        }
    });

    /* CGL-MOOC-Builder:
     * Control Files, Resources, Activity tabs in lesson page(unit.html) */
    $(".course-materials").hide();                  // Initially hide all content
    $("#course-tabs li:first").attr("id","current");// Activate first tab
    $("#course-content div:first").fadeIn();        // Show first tab content
    $('#course-tabs a').click(function(e) {
        e.preventDefault();
        if ($(this).closest("li").attr("id") == "current"){ // Detection for current tab
            return
        }
        else {
            $(".course-materials").hide();
            $("#course-tabs li").attr("id","");     // Reset id
            $(this).parent().attr("id","current");  // Activate this
            $('#' + $(this).attr('name')).fadeIn(); // Show content for current tab
        }
    });

    /* CGL-MOOC-Builder:
     * Hide/show lesson and unit overview on lesson page(unit.html) */
    $("#unit-button-4, #unit-button-5").click(function(e) {
    if($(this).children("div").hasClass("click-and-show")) {
        $(this).children("div").removeClass("click-and-show");
        $(this).children(".expand-hide").text("+");
    }
    else {
        if($(".description").hasClass("click-and-show")) {
            $(".description").removeClass("click-and-show");
            $(".expand-hide").text("+");
        }
        $(this).children("div").addClass("click-and-show");
        $(this).children(".expand-hide").text("-");
    }
    });
});

/* CGL-MOOC-Builder:
 * Helper function that validates user inputs on registration page(register.html) */
function validate(tag, name, value) {
    var check = false;
    switch(name) {
        case "age":
            if(value.match(/^[1-9][0-9]{0,1}$|^$/) != null) {
                $("#age").removeClass('red-border');
                    check = true;
                }
            else {
                $("#age").addClass('red-border');
                check = false;
            }
            break;
        default:
            check = false;
            break;
    }
    return check;
}

/* CGL-MOOC-Builder:
 * Helper function that shows the lesson description on home page when clicking
 * on lesson title(course_structure.html and course_structure_preview.html)*/
function show_description(tag, index) {
    $(tag).addClass("selected");
    $(tag).siblings().removeClass("selected");
    $(tag).parent().parent().next().find("li").hide();
    $(tag).parent().parent().next().find("li:eq("+index+")").show();
}
