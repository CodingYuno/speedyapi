from .util import str_to_seconds


def update_limits(limits: list, current_time_s: int, obj: dict, discrim: str = -1) -> None | int:
    """
    Updates the current state of rate limits in the provided `obj` dictionary.

    :param limits: A list of limits in the format "<number>/<number> <time word>" e.g. "120/min" or "120/2 min"
    :param current_time_s: The unix timestamp in seconds when the request was recieved
    :param obj: The dictionary where rate limit data is to be / currently is being stored
    :param discrim: A discriminator can be provided if a rate limit should be for multiple users e.g. apikey or ip
    """
    for limit_str in limits or []:

        allowed, time_frame = str_to_seconds(limit_str)  # Convert the rate limit string to integer values

        if discrim in obj:  # Separate rate limit instances should be monitored for each individual discriminator

            if limit_str in obj[discrim]:  # The instance already exists and has rate limit data
                if (new_frame := current_time_s // time_frame) == obj[discrim][limit_str]["frame"]:  # We are still using the same period
                    obj[discrim][limit_str]["count"] += 1  # The request count is increased
                    if obj[discrim][limit_str]["count"] > allowed:
                        return time_frame - current_time_s % time_frame  # The time until the user is no longer throttled
                else:  # A new rate limit period is created
                    obj[discrim][limit_str] = {"frame": new_frame, "count": 1}
            else:  # The instance does not yet exist and so new rate limit data is created for it
                obj[discrim][limit_str] = {"frame": current_time_s // time_frame, "count": 1}

        elif discrim == -1:  # Storage of global rate limits

            if limit_str in obj:
                if (new_frame := current_time_s // time_frame) == obj[limit_str]["frame"]:
                    obj[limit_str]["count"] += 1
                    if obj[limit_str]["count"] > allowed:
                        return time_frame - current_time_s % time_frame
                else:
                    obj[limit_str] = {"frame": new_frame, "count": 1}
            else:
                obj[limit_str] = {"frame": current_time_s // time_frame, "count": 1}

        elif discrim is not None:  # Creation of new rate limit instance with new rate limit data
            obj[discrim] = {limit_str: {"frame": current_time_s // time_frame, "count": 1}}
