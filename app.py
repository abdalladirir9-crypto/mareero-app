# --- MANAGER TAB ---
with tab_manager:
    password = st.text_input("Geli Furaha (Password)", type="password")
    
    if password == "mareero2025":
        st.success("🔓 Soo dhawoow Maamule")
        
        # Load Data
        try:
            df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
            df = df.dropna(how="all")
        except:
            df = pd.DataFrame() 

        if not df.empty:
            # 1. LIVE METRICS
            m1, m2, m3 = st.columns(3)
            m1.metric("Wadarta Guud", len(df))
            m2.metric("Alaabta Maqan", len(df[df['Category'] == 'Maqan']) if 'Category' in df.columns else 0)
            m3.metric("Dalabyada Cusub", len(df[df['Category'] == 'Dalab Cusub']) if 'Category' in df.columns else 0)
            
            st.divider()
            
            # 2. DOWNLOAD BUTTONS
            st.subheader("📄 Warbixinada (Reports)")
            col_pdf, col_xls = st.columns(2)
            
            with col_pdf:
                if st.button("Download PDF Report"):
                    with st.spinner("Samaynaya PDF..."):
                        try:
                            pdf_bytes = generate_pdf(df)
                            st.download_button(
                                label="📥 Click to Save PDF",
                                data=pdf_bytes,
                                file_name=f"Mareero_Report_{datetime.now().date()}.pdf",
                                mime="application/pdf"
                            )
                        except Exception as e:
                            st.error(f"Error generating PDF: {e}")
            
            with col_xls:
                if st.button("Download Excel Data"):
                    with st.spinner("Samaynaya Excel..."):
                        xls_bytes = generate_excel(df)
                        st.download_button(
                            label="📥 Click to Save Excel",
                            data=xls_bytes,
                            file_name=f"Mareero_Data_{datetime.now().date()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

            st.divider()

            # 3. EDIT / DELETE SECTION
            st.subheader("🛠️ Wax ka bedel / Tirtir (Edit/Delete)")
            
            # A. Add a temporary 'Delete' column for the checkboxes
            df_with_delete = df.copy()
            df_with_delete.insert(0, "Delete", False)

            # B. The Data Editor
            edited_df = st.data_editor(
                df_with_delete,
                num_rows="fixed", # This hides the messy toolbar icons
                hide_index=True,  # This hides the 0, 1, 2 numbers (The "hera")
                use_container_width=True,
                key="data_editor",
                column_config={
                    "Delete": st.column_config.CheckboxColumn(
                        "Tirtir?",
                        help="Select rows to delete",
                        default=False,
                    )
                }
            )
            
            # C. The Action Buttons
            col_save, col_delete = st.columns([1, 1])

            with col_save:
                if st.button("💾 Kaydi Isbedelka (Save Edits)"):
                    try:
                        # Remove the 'Delete' column before saving
                        final_df = edited_df.drop(columns=["Delete"])
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=final_df)
                        st.cache_data.clear()
                        st.success("✅ Updated Successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            with col_delete:
                # The DELETE Button (Red)
                if st.button("🗑️ Delete Selected Rows", type="primary"):
                    try:
                        # 1. Filter out the rows where 'Delete' is True
                        rows_to_keep = edited_df[edited_df["Delete"] == False]
                        
                        # 2. Drop the 'Delete' column so we don't save it to Google Sheets
                        final_df = rows_to_keep.drop(columns=["Delete"])
                        
                        # 3. Update Google Sheets
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=final_df)
                        
                        st.cache_data.clear()
                        st.success("✅ Items Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting: {e}")

        else:
            st.warning("⚠️ Xog ma jiro (No Data Found)")
            
    elif password:
        st.error("Furaha waa khalad (Wrong Password)")
