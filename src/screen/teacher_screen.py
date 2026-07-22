# Here Inside this src folder, we write all our project source code actually
# This screens folder contains the screens or webpages for teachers, student and home page

# This is teacher login page.

import streamlit as st
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.ui.base_layout import  style_base_layout, style_background_dashboard

from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects, get_attendance_for_teacher
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photos import add_photos_dialog
from src.components.dialog_attendance_results import attendance_result_dialog
from src.components.dialog_voice_attendance import voice_attendance_dialog

import numpy as np
import pandas as pd
from src.database.config import supabase  # here we are importing the instance of supabase client, which we have created in the config.py file, so that we can use that client to interact with our supabase database in our project
from src.pipelines.face_pipeline import predict_attendance

from datetime import datetime   


def teacher_screen():

    style_background_dashboard()
    style_base_layout()


    if "teacher_data" in st.session_state:  # here this teacher_data session variable will contain the data of the currently logged in teacher, so if this session variable is present in the st.session_state, then it means that teacher is logged in and we can show the teacher dashboard screen to the teacher, so here we are checking that if "teacher_data" session variable is present in st.session_state or not, if it is present, then we will show the teacher dashboard screen to the teacher
        teacher_dashboard()
    # Now we will create a session state variable for login which will show what is the type of teacher login
    elif 'teacher_login_type' not in st.session_state  or  st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()
    


def teacher_dashboard():
    teacher_data = st.session_state.teacher_data  # here this teacher_data session variable will contain the data of the currently logged in teacher, so we can use this data to show the teacher name on the dashboard screen and also we can use this data to fetch the attendance data of that teacher from the database and then we can show that attendance data on the dashboard screen to the teacher

    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')

    with c1:
        header_dashboard()

    with c2:
        # st.subheader(f"""Welcome, {teacher_data['name']}!""")    # it just uses the default h3 tag 
        # ---------OR------------
        st.markdown(f"""
            <div style='display: flex;  align-items: center;  justify-content: center;'>
                <h3 style='color: #1e1e1e;  text-align: center'> Welcome, {teacher_data['name']}! </h3>
            </div>
            """,
            unsafe_allow_html=True
        ) 

        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace", width='stretch'):
            st.session_state['is_logged_in'] = False  
            del st.session_state.teacher_data       # This removes the key teacher_data (and its value) from the session state.
            # After this line runs, trying to access st.session_state.teacher_data will raise a KeyError because it no longer exists.
            st.rerun()   # as here state is changing, so we need to rerun it


    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'

    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        type1 = "primary"  if st.session_state.current_teacher_tab == "take_attendance" else "tertiary"
        if st.button('Take Attendance', type=type1,  width='stretch',  icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary"  if st.session_state.current_teacher_tab == "manage_subjects" else "tertiary"
        if st.button('Manage subjects', type=type2,  width='stretch',  icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()
        
    with tab3:
        type3 = "primary"  if st.session_state.current_teacher_tab == "attendance_records" else "tertiary"
        if st.button('Attendance Records', type=type3,  width='stretch',  icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()
 

    footer_dashboard()




def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']

    # st.header("Take AI Attendance")    # it just uses the default h2 tag 
    # ---------OR------------
    st.markdown(f"""
        <div style='display: flex;  align-items: center;  justify-content: center;'>
            <h2 style='color: #1e1e1e;  text-align: center'> Take AI Attendance </h2>
        </div>
        """,
        unsafe_allow_html=True
    ) 


    # Now we will create a state in session_state for storing all the attendance images currently we have
    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []    # at first this attendance_images state will not have any image inside it i.e empty array

    subjects = get_teacher_subjects(teacher_id)    # it will give all the subjects of this teacher_id teacher

    if not subjects:   # if no subjects exists
        st.warning("You haven't created any subjects yet! Please create one to begin!")
        return    # this return is there to stop execution early if no subjects exist, so the rest of the function doesn’t run with invalid or missing data.
    
    # But if subjects exists, then we will show options of these subjects
    # Create a mapping of "SubjectName - SubjectCode" → subject_id
    subject_options = {f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects}

    # Create two columns with a 3:1 width ratio.
    # col1 takes up three parts, col2 takes up one part.
    # Align both columns' content to the bottom for consistent layout.
    # Here vertical_alignment='bottom' → ensures that the content inside both columns aligns at the bottom, which is useful if one column has more content than the other.
    col1, col2 = st.columns([3,1], vertical_alignment='bottom')

    with col1:
        # st.selectbox() in Streamlit is used to create a dropdown menu where users can select one option from a list.
        # In this we need to pass a list of options also
        selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()))
        # The string label the user picked gets stored in selected_subject_label.

    with col2:
        if st.button('Add Photos', type='primary', icon=":material/photo_prints:", width='stretch'):
            add_photos_dialog()

        
    # Now we will find the details of this selected subject
    selected_subject_id = subject_options[selected_subject_label]

    st.divider()

    # now if photos present inside this attendance_images then we will firstly show all those photos    
    if st.session_state.attendance_images:
        # st.header("Added Photos")    # it just uses the default h2 tag 
        # ---------OR------------
        st.markdown(f"""
            <div style='display: flex;  align-items: center;  justify-content: center;'>
                <h2 style='color: #1e1e1e;  text-align: center'> Added Photos </h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Create a gallery layout with 4 columns.
        gallery_cols = st.columns(4)    # list of 4 columns

        # Loop through all attendance images stored in session_state. And Place each image into one of the 4 columns, cycling across columns using idx % 4 to distribute images evenly.
        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, width='stretch', caption=f"Photo {idx+1}")   # it will display each attendance image inside the gallery layout

    # here we will check whether photos exists or not firstly
    has_photos = bool(st.session_state.attendance_images)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button('Clear all photos', width='stretch', type='tertiary', icon=":material/delete:", disabled= not has_photos):
            st.session_state.attendance_images = []
            st.rerun()   # to manage the changes visible

    with c2:
        if st.button('Run Face Analysis', width='stretch', type='secondary', icon=":material/analytics:", disabled= not has_photos):
            # here we are adding this spinner till deep scaning of these photos is happening
            with st.spinner("Deep scanning classroom photos..."):
                all_detected_ids = {}   

                for idx, img in enumerate(st.session_state.attendance_images):
                    # here we will firstly convert the image into RGB, so that we can easily process it
                    # Although we haven't convert the image to RGB during student register using camera, but if we want we can also do this at that time also as it makes things easier for our ML model
                    # All these images inside attendance_images are in proper format which we stored using Image.open(), so no need to do that again here
                    # here we are converting these images to RGB because some images also present in RGBA & some in RBG, which can cause problems, that's why we are converting all of them to RGB only
                    img_numpy = np.array(img.convert('RGB'))

                    # Now we will predict the attendace for these photos
                    detected, _, _ = predict_attendance(img_numpy)    # here _, _ means that we don't have need of these two values, so we are just ignoring them

                    if detected:  # is some student attendance detected
                        for sid in detected.keys():
                            student_id = int(sid)     # # Convert the string key (sid) into an integer student_id

                            # setdefault(student_id, []) → if student_id isn’t already a key in all_detected_id, it creates one with an empty list.
                            # .append(f"Photo {idx+1}") → adds the photo label to that student’s list, so you know which photos were recognized as them.
                            all_detected_ids.setdefault(student_id, []).append(f"Photo {idx+1}")

                
                # it will give all the students enrolled in this current subject
                enrolled_res = supabase.table('subject_students').select("*, students(*)").eq('subject_id', selected_subject_id).execute()
                # Query the 'subject_students' table and also join related data from the 'subjects' table.
                # select('*, subjects(*)') → fetches all columns from subject_students (*) and expands the subjects table (*) for each matching record
                # eq('subject_id', selected_subject_id) → filters rows so only those belonging to the given selected_subject_id are returned

                enrolled_students = enrolled_res.data    # it will give all the students enrolled in this subject

                if not enrolled_students:   # no students present for this subject
                    st.warning("No students enrolled in this course")
                    return   # stop here, don't continue
                

                # but if students present in this course
                # currently we are taking both to me empty
                results, attendance_to_log = [], []

                # it is used to mark the timestamp for attendace taken
                current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                # Here datetime.now() → gets the current local date and time.
                # And .strftime(...) → converts it into a formatted string.
                # %Y → 4‑digit year (e.g., 2026).
                # %m → 2‑digit month. And %d → 2‑digit day.
                # T → literal character T (common in ISO 8601 formats).
                # %H:%M:%S → hour, minute, second in 24‑hour format.

                for node in enrolled_students:
                    # Each node represents an enrollment record for this subject.
                    # The 'students' field inside node contains the actual student details.
                    student = node['students']

                    # Retrieve the list of photo sources where this student_id was detected.
                    # Returns a list of photo labels if found, or an empty list if not detected.
                    sources = all_detected_ids.get(int(student['student_id']), [])

                    is_present = len(sources) > 0    # if length of sources > 0, then it means that this student is present in more than 1 photos uploaded or given by user. So it means that student is present

                    results.append({
                        "Name": student['name'],
                        "ID": student['student_id'],
                        "Source": ", ".join(sources) if is_present else "-",       #If the student was detected (is_present == True), join all photo labels in sources into a single string (e.g., "Photo 1, Photo 3"). If not detected, store a dash ("-") to indicate absence.
                        "Status": "✅ Present" if is_present else "❌ Absent"
                    })

                    attendance_to_log.append({
                        'student_id': student['student_id'],
                        'subject_id': selected_subject_id,
                        'timestamp': current_timestamp,
                        'is_present': bool(is_present)
                    })

                # Display the attendance results in a dialog and log them.
                # Convert results into a DataFrame for tabular view,
                # and pass attendance_to_log for backend storage.
                attendance_result_dialog(pd.DataFrame(results), attendance_to_log)  

    with c3:
        if st.button('Use Voice Attendance', type='primary', width='stretch', icon=":material/mic:"):
            voice_attendance_dialog(selected_subject_id)





def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']   # here this teacher_data session variable will contain the data of the currently logged in teacher, so we can use this data to get the id of the currently logged in teacher, so that we can use that id to fetch the subjects created by that teacher from the database and then we can show those subjects on the manage subjects tab of the dashboard screen to the teacher

    col1, col2 = st.columns(2)

    with col1:
        # st.header("Manage Subjects")    # it just uses the default h2 tag 
        # ---------OR------------
        st.markdown(f"""
            <div style='display: flex;  align-items: center;  justify-content: left;'>
                <h2 style='color: #1e1e1e;  text-align: center'> Manage Subjects </h2>
            </div>
            """,
            unsafe_allow_html=True
        ) 


    with col2:
        if st.button('Create New Subject', width='stretch'):
            create_subject_dialog(teacher_id)


    # List ALL Subjects
    subjects = get_teacher_subjects(teacher_id)

    if subjects:
        for sub in subjects:
            stats = [
                ("👥", "Students", sub['total_students']),
                ("🕰️", "Classes", sub['total_classes']),
            ]

            # here we are creating a share button for each subject, so that teacher can share the subject code with their students, so that students can use that subject code to join that subject and then they can take attendance for that subject using FaceID on the student screen of our app, so here we are creating a share button for each subject, and when the teacher clicks on that button, then it will open a dialog box which will show the subject code and also it will have a copy button to copy that subject code to clipboard, so that teacher can easily share that subject code with their students.
            def share_btn(current_sub=sub):
                # Here we are defining this share_btn() function which will return a button component with the label "Share Code: {subject name}" and when the teacher clicks on that button, then it will open a dialog box which will show the subject code and also it will have a copy button to copy that subject code to clipboard, so that teacher can easily share that subject code with their students.
                if st.button(f"Share Code: {current_sub['name']}", key=f"share_{current_sub['subject_code']}", type='secondary', icon=':material/share:'):
                    share_subject_dialog(current_sub['name'], current_sub['subject_code'])

                st.space()

            subject_card(
                name = sub['name'],
                code = sub['subject_code'],
                section = sub['section'],
                stats = stats,   # here stats means the extra values that we want to show
                footer_callback = share_btn
            )

    else:
        st.info("NO SUBJECTS FOUND. CREATE ONE ABOVE")




# THis fn will show the attendance records for each teacher for each of the subjects teacher taught
def teacher_tab_attendance_records():
    # st.header("Attendance Records")    # it just uses the default h2 tag 
    # ---------OR------------
    st.markdown(f"""
        <div style='display: flex;  align-items: center;  justify-content: center;'>
            <h2 style='color: #1e1e1e;  text-align: center'> Attendance Records </h2>
        </div>
        """,
        unsafe_allow_html=True
    ) 

    teacher_id = st.session_state.teacher_data['teacher_id']

    # here this get_attendance_for_teacher() will run a database query to get us the teacher attendance records
    records = get_attendance_for_teacher(teacher_id)

    if not records:     # it no records exists
        st.warning("No Attendance Records exists!, Please take attendance first")
        return   # we will simply return i.e stop the further flow
    
    # But if some records found, then we need to proceed further
    data = []

    for r in records:
        ts = r.get('timestamp')    # here we are getting the timestamps

        data.append({
            # Extract the timestamp value and normalize it by removing the milliseconds part.
            # Reason: attendance_logs timestamps often include fractional seconds (e.g., "2026-05-23 09:57:10.123456+00").
            # When grouping records by timestamp, these millisecond differences would cause identical events to be treated as separate groups.
            # ts.split(".")[0] → splits the timestamp string at the '.' and keeps only the portion before it (date + time up to seconds).
            # if ts else None → ensures that if ts is missing or None, we safely store None instead of raising an error.
            "ts_group": ts.split(".")[0] if ts else None,
            # Format the timestamp into a human‑readable string for display.
            # datetime.fromisoformat(ts) → parses the ISO 8601 timestamp string (e.g., "2026-05-23 09:57:10+00") into a Python datetime object.
            # strftime("%Y-%m-%d %I:%M %p") → converts the datetime into the format "YYYY-MM-DD HH:MM AM/PM".
            # Example: "2026-05-23 09:57:10+00" → "2026-05-23 09:57 AM".
            # if ts else "N/A" → ensures that if ts is None or missing, we store "N/A" (Not Available) instead of raising an error.
            "Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N/A",
            "Subject": r['subjects']['name'],
            "Subject Code": r['subjects']['subject_code'],
            "is_present": bool(r.get('is_present', False))
        })

    # Now we are creating the dataframe from this data, so that we can apply easily the aggregates function on this
    df = pd.DataFrame(data)


    # Build a summary DataFrame by grouping and aggregating attendance data.
    # df.groupby(['ts_group', 'Time', 'Subject', 'Subject Code']) →
    #     groups the records based on timestamp (normalized without milliseconds), formatted time string,
    #     subject name, and subject code. Each unique combination forms a group.
    # .agg(...) →
    #     applies aggregation functions to each group:
    #       Present_count = ('is_present', 'sum') → counts how many students are marked present
    #       Total_Count   = ('is_present', 'count') → counts total attendance records in the group
    # .reset_index() →
    #     flattens the grouped index back into columns so the result is a clean DataFrame.
    summary = (
        df.groupby(['ts_group', 'Time', 'Subject', 'Subject Code']).agg(
            Present_Count = ('is_present', 'sum'),     # so if is_present = 1, then only it will get added in sum
            Total_Count = ('is_present', 'count')      # so even if is_present is 0 or 1, it gets counted
        ).reset_index()
    )
    # so if 4 students have enrolled, & in photo only 2 are present, then Present_count give 2 and Total_count gives 4 actually

    # Adding this extra column in summary df
    summary['Attendance Stats'] = (
        "✅ " + summary['Present_Count'].astype(str) + " /" + summary['Total_Count'].astype(str) + ' Students'
    )

    # Prepare the final DataFrame for display by sorting and selecting relevant columns.
    # summary.sort_values(by='ts_group', ascending=False) → sorts the grouped attendance summary in descending order of ts_group (latest timestamps first).
    # [['Time', 'Subject', 'Subject Code', 'Attendance Stats']] → selects only the key columns needed for display: formatted time, subject name, subject code, and attendance statistics.
    # The result is a clean, ordered DataFrame ready to be shown in the dashboard.
    display_df = ( summary.sort_values(by='ts_group', ascending=False)[['Time', 'Subject', 'Subject Code', 'Attendance Stats']] )

    st.dataframe(display_df, width='stretch', hide_index=True)




def login_teacher(username, password):
    if not username or not password:   # here we are checking that if username or password is empty, then we will return false, because both username and password are required for login
        return False
    
    teacher = teacher_login(username, password)   # here this teacher_login() function will check that the teacher with this username and password exists in the database or not, if it returns something, then it means that teacher with this username and password exists in the database, so we will return that teacher record, otherwise it will return None

    if teacher:   # if this teacher variable is not None, then it means that teacher with this username and password exists in the database, so we will return true, otherwise we will return false
        st.session_state.user_role = "teacher"   # so here we are setting this user_role session variable to "teacher", so that we can use this session variable to check the role of the currently logged in user in other parts of the app, so that we can show different UI to the teacher and different UI to the student based on their role   
        st.session_state.teacher_data = teacher   # so here we are setting this teacher_data session variable to the data of the currently logged in teacher, so that we can use this data to show the teacher name on the dashboard screen and also we can use this data to fetch the attendance data of that teacher from the database and then we can show that attendance data on the dashboard screen to the teacher
        st.session_state.is_logged_in = True   # so here we are setting this is_logged_in session variable to true, so that we can use this session variable to check whether any user is logged in or not in other parts of the app, so that we can show different UI to the logged in user and different UI to the non-logged in user based on their login status
        return True
    
    return False


def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')

    with c1:
        header_dashboard()

    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None    # so now it will show the home screen as for home screen login_type is set to None actually
            st.rerun()   # as here state is changing, so we need to rerun it


    # st.header('Login using password')    # it just uses the default h2 tag 
    # ---------OR------------
    st.markdown(f"""
        <div style='display: flex;  align-items: center;  justify-content: center;'>
            <h2 style='color: #1e1e1e;  text-align: center'> Login using password </h2>
        </div>
        """,
        unsafe_allow_html=True
    ) 

    st.space()    # similar to <br> tag
    st.space()

    teacher_username = st.text_input("Enter username", placeholder='@arpitpal')

    teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter your password")

    st.divider()    # it adds a horizontal line similar to <hr> tag


    btncol1, btncol2 = st.columns(2)

    with btncol1:
        if st.button('Login', icon=':material/passkey:',  shortcut="control+enter",  width='stretch'):
            if login_teacher(teacher_username, teacher_pass):  # here this login_teacher() function will check that the teacher with this username and password exists in the database or not, if it returns something, then it means that teacher with this username and password exists in the database, so we will set the login type to 'teacher' and then we will show a toast message "welcome back!" with a waving hand emoji and then after some time we will rerun the app, so that it will starts with the entry point of app.py and then it will check the login type and then it will show the teacher dashboard screen as for teacher login type is set to 'teacher' now
                st.toast("welcome back!", icon="👋")  # toast is actually a small notification that appears on the screen
                import time
                time.sleep(1)   # it will wait for 1 second before executing the next line of code, so that user can see the toast message for 1 second
                st.rerun()   # as here state is changing, so we need to rerun it
            else:
                st.error("Invalid username and password combo!")

    with btncol2:
        if st.button('Register Instead', type='primary',  icon=':material/passkey:',  width='stretch'):
            st.session_state.teacher_login_type = "register"


    footer_dashboard()



def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    # here it will check that all the fields are filled or not, if any of the field is empty, then it will return false with a message "All fields are required"
    if not teacher_username  or  not teacher_name  or  not teacher_pass  or  not teacher_pass_confirm:
        return False, "All Fields are required!"
    if check_teacher_exists(teacher_username):   # here this fn check_teacher_exists() will check that the teacher with this username already exists in the database or not, if it returns true, then it means that teacher with this username already exists in the database, so we will return false with a message "Username already taken"
        return False, "Username already taken"
    if teacher_pass != teacher_pass_confirm:
        return False, "Password doesn't match"
    
    # Here we need to put this create_teacher() function inside try catch block because it may throw some error if there is some problem with database connection or something else, so to handle that error, we need to put it inside try catch block
    try:
        # Here we are calling this create_teacher() function from db.py file to create a new teacher in the database with the given username, name and password, so we need to pass these parameters to that function, so that it can create a new teacher in the database with these details
        create_teacher(teacher_username, teacher_pass, teacher_name)
        # so if teacher is created successfully, then it will return true with a message "Successfully Created! Login Now"
        return True, "Successfully Created! Login Now"
    except Exception as e:
        return False, "Unexpected Error!"



def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')

    with c1:
        header_dashboard()

    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None    # so now it will show the home screen as for home screen login_type is set to None actually
            st.rerun()   # as here state is changing, so we need to rerun it


    # st.header('Register your teacher profile')    # it just uses the default h2 tag 
    # ---------OR------------
    st.markdown(f"""
        <div style='display: flex;  align-items: center;  justify-content: center;'>
            <h2 style='color: #1e1e1e;'> Register your teacher profile </h2>
        </div>
        """,
        unsafe_allow_html=True
    ) 

    st.space()    # similar to <br> tag
    st.space()

    teacher_username = st.text_input("Enter username", placeholder='@arpitpal')

    teacher_name = st.text_input("Enter name", placeholder='Arpit Pal')
    
    teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter your password")

    teacher_pass_confirm = st.text_input("Confirm your password", type='password', placeholder="Enter your password")
    
    st.divider()    # it adds a horizontal line similar to <hr> tag


    btncol1, btncol2 = st.columns(2)

    with btncol1:   # since default type of button is 'secondary', so we don't need to write type='secondary' here, it will automatically consider it as secondary button
        if st.button('Register now', icon=':material/passkey:',  shortcut="control+enter",  width='stretch'):
            success, message = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)

            if success:   # if success is true, then it means that teacher is registered successfully, so we will show the success message and then after some time we will set the teacher_login_type to "login", so that it will show the login screen to the teacher, so that teacher can login with the newly created profile
                st.success(message) # it will show the success message in green color
                import time
                time.sleep(2)   # it will wait for 2 seconds before executing the next line of code, so that user can see the success message for 2 seconds
                st.session_state.teacher_login_type = "login"   # so after successful registration, it will set the teacher_login_type to "login", so that it will show the login screen to the teacher, so that teacher can login with the newly created profile
                st.rerun()   # as here state is changing, so we need to rerun it
            else:
                st.error(message)   # it will show the error message in red color

    with btncol2:
        if st.button('Login Instead', type='primary',  icon=':material/passkey:',  width='stretch'):
            st.session_state.teacher_login_type = "login"


    footer_dashboard()