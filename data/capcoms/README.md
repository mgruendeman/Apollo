# Capsule communicators, for a mission without a journal

`apolloNN.json`: `[["HHH:MM", "Name"], ...]`, moments at which the transcript or the tapes name who is
on as CapCom (a crew member's "Okay, Ron."; the announcer's "CapCom is astronaut Stu Roosa"). The
aligner (`aligner/common.py`, `capcom_names`) gives a CC line the nearest named moment within four
hours, else plain "CapCom". Apollo 9's CapComs were Stu Roosa, Ron Evans and Al Worden; its list was
pulled from the crew's own words in NASA's transcript ("Okay, Ron.") and the announcer's shift announcements on the tapes ("Ron Evans has taken over the Capcom duties from Stu Roosa"), read over by hand.
