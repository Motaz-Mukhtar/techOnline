# E-ommerce Website (tecnOnline)

E-commerce Online Store that allow users to showcase there tech products,

Imagine yourself as an senior in software engineer with knowledge of all best practises working on a e-commerce website (tecnOnline).


## Rules

# General

- Follow the code style don't go out of the context.

- add docstrings on each function or API endpoint.

- Every time a user try to access a protected route, make sure to check if the user have the right token, if not redirect
  to the login page.

- And also in every integration you make, check the file API_SPECIFICATION.md to make sure you are passing the correct
  data.

# Front-End

- Make sure to use the primary color in every page, don't use any external color excpet the primary ones

- The design must be like an e-commerce website, with a clean and modern look.

- Don't forget to add the loading animation in every page you create and when fetching data from
  the backend.b

- for any in-app messages or an action like success or error, make sure to show them in a clean and modern way.

# Back-End

- Make sure to validate the input data in every API endpoint, don't trust the client-side validation.

- Make sure that the token are passed in every endpoint at the client-side.

- And make sure to check the token that are coming for the admin endpoint API, the admin have a unique token with
    attribute "role: 'admin'", 