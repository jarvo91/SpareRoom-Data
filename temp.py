#   METHOD TO EXTRACT DATA ABOUT ROOM-SEEKERS & SORT IT INTO A DICTIONARY

def get_combined_seekers(area, seekers={}):
    global buddies_preferences
    buddies_preferences['page'] = 1
    buddies_preferences['where'] = area.lower() # str.lower() makes it lowercase

    params = '&'.join(['{key}={value}'.format(
            key=key, value=buddies_preferences[key]) for key in buddies_preferences])
    flatmates_url = '{location}/{endpoint}?{params}'.format(
            location=api_location, endpoint=api_looking_endpoint, params=params)
    try:
        flatmates_results = json.loads(make_get_request(flatmates_url, cookies=cookies, headers=headers))
    except Exception as e:
        print('Error Getting {area}: {message} (skipping...)'.format(area=area, message=e.message))
        return seekers
    if flatmates_results['success'] == 0 :
        print(area, ' is not a valid search area for Room Seekers: IGNORED')
        return seekers
    if int(flatmates_results['count']) > 10000 : #if there are more than 10k results, there must be an error: exclude this area
        print(area, ' is not returning valid search results for Room Seekers: IGNORED')
        return seekers

    pages = int(flatmates_results['pages']) if 'pages' in flatmates_results else 0
    count = int(flatmates_results['count']) if 'count' in flatmates_results else 0

    if not seekers: # if the dictionary is empty, initialise it
        seekers['listings'] = {}
        seekers['areas'] = { area : count }

    seekers['areas'] = {**seekers['areas'], **{area: count } }

    for page in range(1, min(pages, max_pages)+1):
        preferences['page'] = page

        # prepare url for page request and query the website
        params = '&'.join(['{key}={value}'.format(
            key=key, value=buddies_preferences[key]) for key in buddies_preferences])
        flatmates_url = '{location}/{endpoint}?{params}'.format(
            location=api_location, endpoint=api_looking_endpoint, params=params)
        flatmates_results = json.loads(make_get_request(flatmates_url, cookies=cookies, headers=headers))

        for flatmate_data in flatmates_results['results']: #iterate through listings
            #print(room_data,'\n') # checkpoint
            seeker_id = flatmate_data['advert_id']
            rooms_wanted = int(flatmate_data['number_of_rooms_required']) if 'number_of_rooms_required' in flatmate_data else 1
            combined_b = int(flatmate_data['combined_budget']) if 'combined_budget' in flatmate_data else 0
            couples = True if flatmate_data['couples'] == 'Y' else False
            img = flatmate_data['main_image_square_url'] if 'main_image_square_url' in flatmate_data else None
            # if the seeker is also looking in previously checked areas,
            # simply keep track of this in his data
            if seeker_id in seekers['listings']:
                seekers['listings'][seeker_id]['searching_in'].append(area)
            else:
                seekers['listings'][seeker_id] = {
                                        'ad_id':seeker_id,
                                        'name': flatmate_data['advertiser_name'] if 'advertiser_name' in flatmate_data else 'unspecified',
                                        'rooms_wanted':rooms_wanted,
                                        'searching_in':[area],
                                        'combined_budget':combined_b,
                                        'timestamp' : datetime.now().isoformat(), #ISO 8601 format: YYYY-MM-DDTHH:MM:SS
                                        'couple': couples,
                                        'img':img,
                                        'matching_search_areas' : flatmate_data['example_matching_area'].split(',') if\
                                                    'example_matching_area' in flatmate_data else [area]
                                    }
    return seekers

    # =============================================================================

    # wrapper to search for:
    # 1 - rooms in a given area and then save them to a json file
    # 2 - people looking for a room in the same area
    def get_rooms(areas):
        global rooms
        global people_looking

        for area in areas:
            rooms = {**rooms, **search_rooms_in(area)} # merge dictionaries
            print(rooms)
            people_looking = get_combined_seekers(area, people_looking)

            temp_dict1, temp_dict2 = get_combined_seekers(area)
            people_looking['listings'] = {**temp_dict1, **people_looking['listings']}
            people_looking['areas'] = {**temp_dict2, **people_looking['areas']}

        save_flatmates(people_looking)
        save_rooms(rooms)
