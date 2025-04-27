
# ED Joy

Elite Dangerous Joystick Monitor

A modern version of [ED:Runner](https://forums.frontier.co.uk/threads/ed-runner-a-help-program-for-vr-headsets-with-joysticks-hotas-part-2.440760/) written in Python. ED Joy will monitor your selected joysticks and redirect focus back to Elite Dangerous so that your joysticks continue to control Elite are able to continue playing regardless of your focused application.

While all Joystick/HOTAS should work without issue, the following are confirmed working:
- Saitek X56 Rhino

## Roadmap
- [X] Detect & monitor joysticks
- [X] Functional threaded UI
- [X] Mark joystick for monitoring
- [X] Save/load settings
- [ ] List running apps/determine focused application
- [ ] Set focused application
- [ ] Launch additional apps when Elite Dangerous is running
- [ ] Terminate launched apps when Elite Dangerous is closed
- [ ] Check for updates
- [ ] Bundle as .exe


If you have a feature request, please raise it as an **issue**



### Requirements

- [Python 3.13.2](https://www.python.org/)

<!-- ## Getting Started

TBD -->
<!-- 
### Installing

A step by step series of examples that tell you how to get a development
environment running

Say what the step will be

    Give the example

And repeat

    until finished

End with an example of getting some data out of the system or using it
for a little demo -->

<!-- ## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code
of conduct, and the process for submitting pull requests to us. -->

## Versioning

We use [Semantic Versioning](http://semver.org/) for versioning. <!--For the versions
available, see the [tags on this
repository](https://github.com/CitizenStile/a-good-readme-template/tags).-->

## License

This project is licensed under the MIT
License - see the [LICENSE.md](LICENSE.md) file for
details

## Change Log:

### 0.2.0:
- Updating readme
- Cleanup UI
- Implement settings
### 0.1.0:
- Initial release to poll joysticks for input
- Threaded UI