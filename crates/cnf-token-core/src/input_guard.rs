pub fn sanitize(input: &str) -> String {
    input.replace('\r', "").replace('\n', " ")
}
