rand=$(date +%s)
if [ -d src/static/css ]; then
    rm -r src/static/css
fi
mkdir src/static/css

sass="sass"
source="src/assets/scss/main.scss"
out_path="src/static/css/"
main="main"
output="$out_path$main$rand.css"

command="$sass $source $output"
eval $command
css_suffix="css_suffix"
echo "$rand" > "css_suffix.txt"
