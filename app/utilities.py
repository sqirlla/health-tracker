"""
The Health Tracker application is an easy way for organizations to record and 
manage the daily vital readings of their employees, partners, contractors, etc. 
in response to the COVID-19 pandemic. 

Copyright (C) 2020 Sqirl, LLC

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Please refer to LICENSE in the project repository for details.
"""
from config import Config
from datetime import datetime, timedelta, date
from pytz import timezone
import io
import pytz
import csv
import re

class Utilities:
    """
    Utilities are a collection of commonly used functions which have minimal 
    dependencies on the core application and do not logically fit in a particular 
    Model. 
    """
    def get_date():
        """
        get_date returns a YYYY-mm-dd string that is localized to the 
        timezone set in the app's config variables. 
        If no timezone is set this app will crash. 
        **As of right now there are no considerations for daylight savings time. 
        This app might give incorrect readings during a timechange, specifically in March and 
        October, but even more so when we "fall back". 
        """
        tz = timezone(Config.TIMEZONE)
        local_date = datetime.now()
        localized_date = tz.localize(local_date)
        str_date = localized_date.strftime("%Y-%m-%d")
        return str_date
    
    def stream_generate_readings(header, contents):
        """
        This func will return a csv stream of all readings, intended to be streamed to the browser 
        for downloading a csv. 
        
        Args:
            header - list of col headings to capture, in order. 
            contents - query object to use as datasource

        Returns:
            StringIO stream 

        This was intended to be generic, allowing for input of any row headers, able to transpose items 
        like 'user_id.id' into the second level relationship structure of the query set and pull values 
        from those dicts. We got as far as identifying and splitting the header keys but could not traverse 
        into the second level obj as the obj was somehow lost. 
        `item.__dict__[match.group('base')]` is how we were accessing the members of the Readings obj programmatically, 
        but the result of that is a string, not a Users obj as expected when looking for Readings.user_id - relationship as 
        defined should make that a Users obj. 
        This might be eligible for a re-write, but it does the job needed for now. 
        """
        data = io.StringIO()
        w = csv.writer(data)

        w.writerow(header)
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        pattern = re.compile('^username$')

        for item in contents:
            row = []
            for i in header:
                match = pattern.match(i)
                if match:
                    row.append(item.get_username())
                else:
                    row.append(item.__dict__[i])
            w.writerow(row)
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)