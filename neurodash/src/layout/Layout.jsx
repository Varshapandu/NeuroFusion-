// import Sidebar from "./Sidebar";
// import Navbar from "./Navbar";
//
// export default function Layout({ currentPage, onNavigate, children }) {
//   return (
//     <div className="flex w-screen h-screen bg-gray-950 text-white ">
//
//       <Sidebar currentPage={currentPage} onNavigate={onNavigate} />
//
//       <div className="flex-1 flex flex-col">
//         <Navbar />
//
//         <div className="flex-1">
//           {children}
//         </div>
//       </div>
//
//     </div>
//   );
// }
//
//
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import bg from "../assets/bg.png";   // universal background

export default function Layout({ currentPage, onNavigate, children }) {
  return (
    <div style={{ position: "relative", minHeight: "100vh", width: "100%" }}>

      {/* 🌌 UNIVERSAL BACKGROUND */}
      <div
        style={{
          position: "fixed",
          inset: 0,
          backgroundImage: `url(${bg})`,
          backgroundSize: "cover",
          backgroundPosition: "top center",
          backgroundRepeat: "no-repeat",
          zIndex: -1,
        }}
      />

      {/* 🧭 APP LAYOUT */}
      <div className="flex min-h-screen w-full text-white">

        {/* Sidebar */}
        <aside className="w-[260px] shrink-0">
          <Sidebar currentPage={currentPage} onNavigate={onNavigate} />
        </aside>

        {/* Main Area */}
        <div className="flex-1 flex flex-col">

          {/* Navbar */}
          <div className="h-16 shrink-0">
            <Navbar />
          </div>

          {/* Page Content */}
          <main className="flex-1 overflow-hidden px-10 py-8">
              {children}
          </main>

        </div>
      </div>
    </div>
  );
}
