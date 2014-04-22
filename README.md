cgl-mooc-builder
================

cgl mooc builder is an open source technology for creating online course that is built on Google Course Builder 1.6.0 with a few modifications:

Course Structure Modifications: We changed the course structure and added another level hierarchy i.e. Section -> Unit -> Lesson Hierarchy. This may be ideal for a 3 credit hour course. We think that it is. It was suited for our 3-credit hour semester long course. Sections can also be divided based on expertise level i.e. beginner, intermediate, expert. Sections can be thought of as part of a series course. A unit many times can be part of the same topic so it made sense for us to combine them under a section.

Lesson Page Modifications. We created a tab bar that is also a bit more scalable. Now the lesson activities, files, resources, and any other additional content can be put on the same page. Our research and testing showed that it made more sense to put activities on the same page as the lesson so it was conveniently located. Context was to perform an activity within the same lesson so that you can refer back to the lesson video while doing the activity rather than making students go back and forth between video lesson page and activity page to complete their activity. Our preliminary primary user research shows that having easy access to course materials is more likely to reduce attrition rate.

Design Changes: We implemented some interface and interaction design changes mainly to provide for a better IXD experience and to make the site look more professional.

Progress Bar: We created a progress bar if you visited a lesson page. This way you can determine if you viewed the entire course. However, this is NOT a robust solution since there is no way to determine if a student actually played the video fully and for what duration. Progress bar data could be used in several ways. One should be able to track his/her progress, compare it against the entire class (optional), integrate this data using Game Theory for example.

In July 2012, Google hosted a 2-week online, community-based course called Power Searching with Google. The course showcased search techniques and how to use them to solve real, everyday problems. We
created Power Searching as a MOOC (Massive Online Open Course) by using a variety of Google's existing products and by writing an App Engine application for the course material and assessments. 

We were quite pleased with the success of Power Searching with Google. Over 154,000 students from 190 countries enrolled in the course. Almost 68,000 of the original registrants got started by filling out a pre-course assessment. And over 20,000 earned a certificate of successful completion.
 
Course Builder Experiment represents our decision to open source the code we used to create Power Searching and to document our use of that code in conjunction with Google products to create the entire
experience. 

Course Builder uses an icon (found at coursebuilder/modules/upload/resources/script_add.png) from the Silk icon set version 1.3 by Mark James, licensed under a Creative Commons Attribution 2.5 license. For more information on Silk, see http://www.famfamfam.com/lab/icons/silk/.

For more information on Course Builder, see the documentation at https://code.google.com/p/course-builder/wiki/CourseBuilderChecklist.
