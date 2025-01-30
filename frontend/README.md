# NextJS frontend with Headless CMS 

In a headless CMS, the frontend is decoupled from the backend, and the frontend can be built with any technology. In this project, we use NextJS as the frontend to display concert data managed by Wagtail CMS.

This frontend simply does the following:
- Display the concert data from Wagtail CMS with HTTP requests, and display it in pages
- The frontend is minimal and only displays the concert data in a card format inside a container

The reason that NextJS is used compared to other frameworks is because:
- Since there will be some time allocation into learning how Wagtail works, choosing a familiar framework like NextJS will help speed up the development process
- NextJS is a React framework that is easy to use and has a lot of community support, and components such as shadcn/ui can be easily used to design a responsive and aesthetic frontend

## Technology used
- NextJS
- shadcn/ui