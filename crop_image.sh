
echo "Uncomment the section you want to run in this bash script. Take extra care running this."

# The final screenshots
# for file in ./**/*.png ; do         # Use ./* ... NEVER bare *
#   if [ -e "$file" ] ; then   # Check whether file exists.
#     echo "Converting $file"
#     cp "$file" "$file-backup.png"
#     convert "$file" -crop 360x640+34+175 "$file"
#   fi
# done

# The intermediates
# for file in ./**/**/[0-9]*.png ; do         # Use ./* ... NEVER bare *
#   if [ -e "$file" ] ; then   # Check whether file exists.
#     echo "Converting $file"
#     # cp "$file" "$file-backup.png"
#     convert "$file" -crop 360x640+34+175 -resize 25% "$file.jpg"
#   fi
# done