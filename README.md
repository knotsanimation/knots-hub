# knots-hub

The highest level software in the Knots studio pipeline. Used directly by
artist to interract with the pipeline.

# design

The hub wraps every other piece of software in use at Knots and ensure they
are properly configured and installed.

The hub is designed for our specific need and might not suit every studio. One
of our major need being to go local-first when possible. Our network infratructure
being pretty minimal we defer of storing as much software possible on the user
local machine to avoid reducing performances.

The hub is reponsible of bootstrapping himself on user machine and installing
any dependency needed. It however needs to be packaged as an self-sufficient 
executable first by a developer, shared on the network to be executed a first 
time by the users. That first execution will install it on the user machine,
and from then the local installation will self-update itself as needed.
