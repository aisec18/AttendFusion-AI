import streamlit as st
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.database.db import check_teacher_exists,create_teacher,teacher_login,get_teacher_subject,create_subject,get_attendance_for_teacher
from src.components.dialog_create_subject import create_subject_dialog
from src.components.subject_card import subject_card
from src.components.dialog_add_photos import add_photos_dialog
from src.components.dialog_share_subject import share_subject_dialog
import numpy as np
from src.pipelines.face_pipeline import predict_attendance
from src.database.config import supabase
from datetime import datetime
import pandas as pd
from src.components.dialog_attendance_results import attendance_result_dialog
from src.components.dialog_voice_attendance import voice_attendance_dialog
def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()

def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    
    # Unique key for login screen back button
    with c2:
        st.subheader(f"""Welcome, {teacher_data['name']}!""")
        if st.button("Logout", type='secondary', key='login_back_btn', shortcut="control+backspace"):
           st.session_state['is_logged_in'] = False
           del st.session_state.teacher_data
           st.rerun()

    st.space()
    
    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"
    tab1,tab2,tab3=st.columns(3)
    with tab1:
        type1="primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('take attendance',width='stretch',type=type1,icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()
    with tab2:
        type2="primary" if st.session_state.current_teacher_tab == 'manage_subject' else "tertiary"
        if st.button('Manage Subjects',width='stretch',type=type2,icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subject'
            st.rerun()
    with tab3:
        type3="primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button('Attendance Records',width='stretch',type=type3,icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()
    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()

    if st.session_state.current_teacher_tab == "manage_subject":
        teacher_tab_manage_subject()
    
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    footer_dashboard()


def teacher_tab_take_attendance():
    teacher_id=st.session_state.teacher_data['teacher_id']
    st.header("Take AI Attendance")
    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []
    subjects=get_teacher_subject(teacher_id)

    if not subjects:
        st.warning('You havent created any subject yet!please create one to begin')
        return
    
    subject_options={f"{s['name']}-{s['subject_code']}": s['subject_id'] for s in subjects}

    col1,col2=st.columns([3,1],vertical_alignment='bottom')
    with col1:
        selected_subject_label=st.selectbox('Select Subject',options=list(subject_options.keys()))
    with col2:
        if st.button('Add photos',type='primary',width='stretch'):
            add_photos_dialog()

    selected_subject_id=subject_options[selected_subject_label]

    st.divider()

    if st.session_state.attendance_images:
        st.header('Added Photos')
        gallery_cols=st.columns(4)
        for idx,img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx%4]:
                st.image(img,width='stretch',caption=f'Photo{idx+1}')
    has_photos=bool(st.session_state.attendance_images)
        
    c1,c2,c3=st.columns(3)
    with c1:
            if st.button('Clear all photos',width='stretch',type='tertiary',disabled=not has_photos):
                st.session_state.attendance_images=[]
                st.rerun()
    with c2:
            if st.button('Run face analysis',width='stretch',type='secondary',disabled=not has_photos):
                with st.spinner('Deep scanning classroom photos'):
                    all_detected_ids={}

                    for idx,img in enumerate(st.session_state.attendance_images):
                        img_np=np.array(img.convert('RGB'))

                        detected,_,_=predict_attendance(img_np)

                        if detected:
                            for sid in detected.keys():
                                student_id=int(sid)

                                all_detected_ids.setdefault(student_id,[]).append(f"Photo {idx+1}")
                    enrolled_res=supabase.table('subject_students').select("*,students(*)").eq('subject_id',selected_subject_id).execute()
                    enrolled_students=enrolled_res.data

                    if not  enrolled_students:
                        st.warning("No students in this course")
                    else:
                        results,attendace_to_log=[],[]
                        current_timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                        for node in enrolled_students:
                            student=node['students']
                            sources=all_detected_ids.get(int(student['student_id']),[])
                            is_present=len(sources)>0

                            results.append({
                                "Name":student['name'],
                                "ID": student['student_id'],
                                "Source": ",".join(sources) if is_present else "-",
                                "Status":"Present" if is_present else "Absent"
                            })
                            attendace_to_log.append({
                                'student_id': student['student_id'],
                                'subject_id': selected_subject_id,
                                'timestamp': current_timestamp,
                                'is_present': bool(is_present)
})
                    attendance_result_dialog(pd.DataFrame(results),attendace_to_log)
                            
    with c3:
            st.button('Use Voice Attendance',type='primary',width='stretch')
            voice_attendance_dialog(selected_subject_id)

def teacher_tab_manage_subject():
    teacher_id=st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns(2)
    with col1:
        st.header('Manage Subjects',width='stretch')
    with col2:
        if st.button('Create new subject',width='content'):
            create_subject_dialog(teacher_id)

    st.header("Manage Subjects")
    subjects=get_teacher_subject(teacher_id)
    if subjects:
        for sub in subjects:
            
                stats = [
                            ("👥", "Students", sub['total_students']),
                            ("📚", "Classes", sub['total_classes']),
                        ]
                def share_btn():
                    if st.button(f"Share Code {sub['name']}",key=f"share_{sub['subject_code']}",type='secondary',icon=':material/share:'):
                        share_subject_dialog(sub['name'],sub['subject_code'])
                    st.space()
                subject_card(
                    name=sub['name'],
                    code=sub['subject_code'],
                    section=sub['section'],
                    stats=stats,
                    footer_callback=share_btn
                )
    else:
        st.info("No subject found,create one above")



def teacher_tab_attendance_records():
    st.header('Attendance Records')
    teacher_id=st.session_state.teacher_data['teacher_id']
    records=get_attendance_for_teacher(teacher_id)
    if not  records:
        return
    
    data=[]
    for r in records:
        ts=r.get('timestamp')
        data.append({
            "ts_group":ts.split(".")[0] if ts else None,
            "Time":datetime.fromisformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N'A", 
            "Subject":r['subjects']['name'],
            "Subject_Code":r['subjects']['subject_code'],
            "is_present":bool(r.get('is_present',False))
        })
    df=pd.DataFrame(data)
    summary=(
        df.groupby(['ts_group','Time',"Subject","Subject_Code","is_present"]).agg(
            Present_count=('is_present','sum'),
            Total_Count=('is_present','count')
        ).reset_index()
    )
    summary['Attendance Stats'] = (
    "✅ " + summary['Present_Count'].astype(str) + " /"
    + summary['Total_Count'].astype(str) + " Students"
    )

    display_df = (
        summary.sort_values(by='ts_group', ascending=False)
        [['Time', 'Subject', 'Subject Code', 'Attendance Stats']]
    )

    st.dataframe(display_df, width='stretch', hide_index=True)

def login_teacher(username, password):
    if not username or not password:
        return False
    teacher=teacher_login(username,password)
    if teacher:
        st.session_state.user_role='teacher'
        st.session_state.teacher_data=teacher
        st.session_state.is_logged_in=True
        return True

def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    
    # Unique key for login screen back button
    with c2:
        if st.button("Go back to Home", type='secondary', key='login_back_btn', shortcut="control+backspace"):
           st.session_state['login_type'] = None
           st.rerun()

    # Centered header using HTML markdown
    st.header('Login Using password', text_alignment='center')
    st.space()
    
    teacher_username = st.text_input("Enter your username", placeholder="Enter your username", label_visibility='collapsed', key='login_teacher_username')
    st.write("") 
    
    teacher_password = st.text_input("Enter your password", placeholder="Enter your password", label_visibility='collapsed', key='login_teacher_password', type='password')
    
    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button("Login", type='secondary', key='teacher_login_submit_btn', shortcut="control+enter", use_container_width=True):
            if login_teacher(teacher_username,teacher_password):
                st.toast("welcome back!",icon="👋")
                import time 
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username")


    with btnc2:
        if st.button("Register Instead", type='primary', key='teacher_goto_register_btn', shortcut="control+backspace", use_container_width=True):
            st.session_state.teacher_login_type = 'register'
            st.rerun()
            
    footer_dashboard()  
    
def register_teacher(teacher_username, teacher_name, teacher_password, teacher_pass_confirm):
    if not teacher_username or not teacher_name or not teacher_password or not teacher_pass_confirm:
        return False, "Please fill in all fields."
    
    if check_teacher_exists(teacher_username):
        return False,"Username already taken"
    
    if teacher_password != teacher_pass_confirm:
        return False, "Passwords do not match."
    
    try:
        create_teacher(teacher_username,  teacher_password,teacher_name)
        return True, "Registration successful!"
    except Exception as e:
        return False,"Unexpected error"
    # Here you would typically add code to save the teacher's information to a database
    # For this example, we'll just simulate a successful registration
  

def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        # Unique key for register screen back button
        if st.button("Go back to Home", type='secondary', key='register_back_btn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    # Centered header using HTML markdown            
    st.markdown("<h2 style='text-align: center;'>Register Your Profile</h2>", unsafe_allow_html=True)
    st.write("") 
    
    teacher_username = st.text_input("Enter your username", placeholder="Enter your username", label_visibility='collapsed', key='reg_teacher_username')
    st.write("") 
    
    teacher_name = st.text_input("Enter your name", placeholder="Enter your name", label_visibility='collapsed', key='reg_teacher_name')
    teacher_password = st.text_input("Enter your password", placeholder="Enter your password", label_visibility='collapsed', key='reg_teacher_password', type='password')
    teacher_pass_confirm = st.text_input("Confirm your password", placeholder="Confirm your password", label_visibility='collapsed', key='reg_teacher_confirm_password', type='password')

    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button("Register", type='secondary', key='teacher_register_submit_btn', shortcut="control+enter", use_container_width=True):     
            success,message=register_teacher(teacher_username, teacher_name, teacher_password, teacher_pass_confirm)
            if success:
                st.success(message)
                import time
                time.sleep(2)
                st.session_state.teacher_login_type="login"
                st.rerun()
            else:
                st.error(message)
    with btnc2:
        if st.button("Login Instead", type='primary', key='teacher_goto_login_btn', shortcut="control+backspace", use_container_width=True):
            st.session_state.teacher_login_type = 'login'
            st.rerun()
            
    footer_dashboard()