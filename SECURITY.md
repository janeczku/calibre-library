# Security Policy

## Reporting a Vulnerability

Please report security issues to ozzie.fernandez.isaacs@googlemail.com

## Supported Versions

To receive fixes for security vulnerabilities it is required to always upgrade to the latest version of Calibre-Web. See https://github.com/janeczku/calibre-web/releases/latest for the latest release.

## History

| Fixed in  | Description  |CVE number |
| ---------- |---------|---------|
| 3rd July 2018 | Guest access acts as a backdoor||
| V 0.6.7 |Hardcoded secret key for sessions |CVE-2020-12627 |
| V 0.6.13|Calibre-Web Metadata cross site scripting |CVE-2021-25964|
| V 0.6.13|Name of Shelves are only visible to users who can access the corresponding shelf Thanks to @ibarrionuevo||
| V 0.6.13|JavaScript could get executed in the description field. Thanks to @ranjit-git  and Hagai Wechsler (WhiteSource)||
| V 0.6.13|JavaScript could get executed in a custom column of type "comment" field ||
| V 0.6.13|JavaScript could get executed after converting a book to another format with a title containing javascript code||
| V 0.6.13|JavaScript could get executed after converting a book to another format with a username containing javascript code||
| V 0.6.13|JavaScript could get executed in the description series, categories or publishers title||
| V 0.6.13|JavaScript could get executed  in the shelf title||
| V 0.6.13|Login with the old session cookie after logout. Thanks to @ibarrionuevo||
| V 0.6.14|CSRF was possible. Thanks to @mik317 and Hagai Wechsler (WhiteSource)  |CVE-2021-25965|
| V 0.6.14|Cross-Site Scripting vulnerability on typeahead inputs. Thanks to @notdodo||


