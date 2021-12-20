#include <string>
#include <memory>
#include <vector>
#include <utility>
#include <iostream>

using std::vector;
using std::string;
using std::iostream;


class User{
    public:
    User() = default;
    User(const string & n, const string & pwd);


    private:
    string password;
    string uname;

};



User::User(const string & n, const string & pwd): password(pwd), uname(n){}


